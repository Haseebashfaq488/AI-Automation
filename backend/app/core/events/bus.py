import asyncio
import logging
import threading
from collections import deque
from collections.abc import Callable
from typing import Any, Dict, List, Optional, Set

from app.core.events.schema import EventType, JarvisEvent

logger = logging.getLogger("jarvis.events.bus")


class GlobalEventBus:
    """Central Async Event Spine for Jarvis.

    Supports:
    - Multi-subscriber SSE queue distribution.
    - Fast in-memory replay buffer for new UI reconnections.
    - Synchronous and asynchronous pub/sub topic listeners.
    - Non-blocking thread-safe dispatch from background workers and threads.
    """

    def __init__(self, history_size: int = 50):
        self._history: deque[JarvisEvent] = deque(maxlen=history_size)
        self._history_lock = threading.Lock()

        # SSE subscriber queues
        self._sse_queues: Set[asyncio.Queue] = set()
        self._sse_lock = threading.Lock()

        # Topic listeners: EventType (or "*") -> List[Callable]
        self._listeners: Dict[str, List[Callable]] = {}
        self._listeners_lock = threading.Lock()

        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Explicitly set or update the main asyncio loop for cross-thread calls."""
        self._loop = loop

    def get_history(self, limit: int = 50) -> List[JarvisEvent]:
        """Return a snapshot of recently published events in chronological order."""
        with self._history_lock:
            items = list(self._history)
        return items[-limit:]

    def subscribe_sse(self) -> asyncio.Queue:
        """Subscribe a new asyncio.Queue to receive live streaming events."""
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        with self._sse_lock:
            self._sse_queues.add(q)
        return q

    def unsubscribe_sse(self, queue: asyncio.Queue) -> None:
        """Remove an asyncio.Queue from active SSE subscribers."""
        with self._sse_lock:
            self._sse_queues.discard(queue)

    def on(self, event_type: str | EventType, callback: Callable) -> None:
        """Register a callback for a specific event type (or '*' for all events)."""
        key = event_type.value if isinstance(event_type, EventType) else str(event_type)
        with self._listeners_lock:
            self._listeners.setdefault(key, []).append(callback)

    def off(self, event_type: str | EventType, callback: Callable) -> None:
        """Unregister a callback."""
        key = event_type.value if isinstance(event_type, EventType) else str(event_type)
        with self._listeners_lock:
            if key in self._listeners:
                try:
                    self._listeners[key].remove(callback)
                except ValueError:
                    pass

    def publish(self, event: JarvisEvent) -> None:
        """Publish an event to all SSE streams and registered topic listeners (thread-safe)."""
        # 1. Record in history ring buffer
        with self._history_lock:
            self._history.append(event)

        # 2. Forward to SSE queues
        with self._sse_lock:
            queues = list(self._sse_queues)

        for q in queues:
            try:
                loop = getattr(q, "_loop", None) or self._loop
                if loop and loop.is_running():
                    loop.call_soon_threadsafe(
                        lambda _q=q, _ev=event: _q.put_nowait(_ev) if not _q.full() else None
                    )
                else:
                    if not q.full():
                        q.put_nowait(event)
            except Exception as exc:
                logger.debug("Failed forwarding event to SSE queue: %s", exc)

        # 3. Trigger topic listeners
        key = event.event_type.value if isinstance(event.event_type, EventType) else str(event.event_type)
        with self._listeners_lock:
            specific_cbs = self._listeners.get(key, []).copy()
            wildcard_cbs = self._listeners.get("*", []).copy()

        all_cbs = specific_cbs + wildcard_cbs
        for cb in all_cbs:
            try:
                res = cb(event)
                if asyncio.iscoroutine(res):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(res)
                    except RuntimeError:
                        if self._loop and self._loop.is_running():
                            asyncio.run_coroutine_threadsafe(res, self._loop)
                        else:
                            try:
                                # Run synchronously to completion if no loop exists
                                cur_loop = asyncio.new_event_loop()
                                cur_loop.run_until_complete(res)
                                cur_loop.close()
                            except Exception:
                                pass
            except Exception as exc:
                logger.error("Error in event listener callback for %s: %s", key, exc, exc_info=True)


# Global singleton instance
_global_event_bus: Optional[GlobalEventBus] = None


def get_event_bus() -> GlobalEventBus:
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = GlobalEventBus()
    return _global_event_bus
