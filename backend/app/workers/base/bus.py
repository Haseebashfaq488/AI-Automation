import asyncio
import json
import threading
from collections.abc import Callable, Coroutine
from typing import Any, Dict, List, Optional

# Global in‑process bus: session_id → list of callbacks (async or sync)
_bus: Dict[str, List[Callable]] = {}
_bus_lock = threading.Lock()

# Global in-process queue bus for SSE live streaming: session_id → list of (asyncio.Queue, asyncio.AbstractEventLoop)
_queues: Dict[str, List[Any]] = {}
_queues_lock = threading.Lock()


def subscribe(session_id: str) -> asyncio.Queue:
    """Subscribe a new asyncio.Queue to receive live streaming events for session_id."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    q: asyncio.Queue = asyncio.Queue(maxsize=1000)
    with _queues_lock:
        _queues.setdefault(session_id, []).append((q, loop))
    return q


def unsubscribe(session_id: str, queue: asyncio.Queue) -> None:
    """Unsubscribe and remove an asyncio.Queue from session_id's active subscribers."""
    with _queues_lock:
        queue_list = _queues.get(session_id, [])
        to_remove = [item for item in queue_list if (item[0] if isinstance(item, tuple) else item) is queue]
        for item in to_remove:
            queue_list.remove(item)
        if not queue_list and session_id in _queues:
            _queues.pop(session_id, None)


def emit_to_queues(session_id: str, event: Dict[str, Any]) -> None:
    """Forward a streaming event to all active async queues subscribed to session_id (thread-safe)."""
    with _queues_lock:
        subscribers = _queues.get(session_id, []).copy()

    for item in subscribers:
        if isinstance(item, tuple):
            q, loop = item
        else:
            q, loop = item, getattr(item, "_loop", None)
        try:
            if loop and loop.is_running():
                loop.call_soon_threadsafe(
                    lambda _q=q, _ev=event: _q.put_nowait(_ev) if not _q.full() else None
                )
            else:
                if not q.full():
                    q.put_nowait(event)
        except Exception:
            pass


def on(session_id: str, callback: Callable) -> None:
    """Register a callback that will be invoked whenever the session emits an event."""
    with _bus_lock:
        _bus.setdefault(session_id, []).append(callback)


def emit(session_id: str, event_type: str, data: dict) -> None:
    """Send an event to all registered callbacks for *session_id*.

    Callbacks may be synchronous or async; we handle both.
    """
    with _bus_lock:
        callbacks = _bus.get(session_id, []).copy()

    for cb in callbacks:
        try:
            result = cb(event_type, data)
            if asyncio.iscoroutine(result):
                # Schedule the coroutine on the running loop (best‑effort)
                try:
                    asyncio.get_event_loop().create_task(result)
                except RuntimeError:
                    # No running loop – fire‑and‑forget
                    pass
        except Exception as exc:
            # Never let a bad callback break the worker loop
            print(f"[worker bus] callback error: {exc}")

    # Forward to global event bus for real-time frontend streaming & orchestrator triggers
    try:
        from app.core.events.bus import get_event_bus
        from app.core.events.schema import EventType, JarvisEvent

        gbus = get_event_bus()
        evt_type_map = {
            "WORK_STARTED": EventType.WORKER_STARTED,
            "STEP_STARTED": EventType.WORKER_STEP_STARTED,
            "STEP_COMPLETED": EventType.WORKER_STEP_COMPLETED,
            "VALIDATION_FAILED": EventType.WORKER_VALIDATION_FAILED,
            "RECOVERY_STARTED": EventType.WORKER_RECOVERY_STARTED,
            "RECOVERY_COMPLETED": EventType.WORKER_RECOVERY_COMPLETED,
            "WORK_COMPLETED": EventType.WORKER_COMPLETED if data.get("success", False) else EventType.WORKER_FAILED,
        }
        ge_type = evt_type_map.get(event_type)
        if ge_type:
            title = f"Worker {session_id[:8]}: {event_type.replace('_', ' ').title()}"
            if event_type == "STEP_STARTED":
                title = f"Worker Step: {data.get('step', 'unknown')}"
                summary = f"Executing step '{data.get('step')}' (index {data.get('index', 0)})"
            elif event_type == "STEP_COMPLETED":
                title = f"Step Completed: {data.get('step', 'unknown')}"
                summary = f"Step '{data.get('step')}' finished."
            elif event_type == "WORK_COMPLETED":
                success = data.get("success", False)
                title = f"Worker Completed [{session_id[:8]}]" if success else f"Worker Failed [{session_id[:8]}]"
                summary = f"Worker finished with {len(data.get('tools_used', []))} steps. Success: {success}"
            else:
                summary = f"Worker event {event_type} on session {session_id}"

            gbus.publish(
                JarvisEvent(
                    event_type=ge_type,
                    source=f"worker:{session_id}",
                    title=title,
                    summary=summary,
                    data={"session_id": session_id, **data},
                    metadata={"session_id": session_id},
                )
            )
    except Exception:
        pass


# ------------------------------------------------------------------
# Helper: auto‑register from the WorkerEngine so the SSE handler can
# simply ``await bus.anew(session_id)`` without manually calling ``on()``.
# ------------------------------------------------------------------


class EventBus:
    """Helper that gives the worker engine a clean ``await bus.xxx`` API."""

    def __init__(self, session_id: str):
        self.session_id = session_id

    # --- event convenience methods ---
    def work_started(self, data: dict = None) -> None:
        emit(self.session_id, "WORK_STARTED", data or {})

    def step_started(self, step_name: str, step_index: int, data: dict = None) -> None:
        emit(
            self.session_id,
            "STEP_STARTED",
            {"step": step_name, "index": step_index, **(data or {})},
        )

    def step_completed(
        self, step_name: str, step_index: int, output: dict = None, errors: list = None
    ) -> None:
        emit(
            self.session_id,
            "STEP_COMPLETED",
            {
                "step": step_name,
                "index": step_index,
                "output": output or {},
                "errors": errors or [],
            },
        )

    def validation_started(self, step_name: str, data: dict = None) -> None:
        emit(
            self.session_id,
            "VALIDATION_STARTED",
            {"step": step_name, **(data or {})},
        )

    def validation_failed(
        self, step_name: str, errors: list, data: dict = None
    ) -> None:
        emit(
            self.session_id,
            "VALIDATION_FAILED",
            {"step": step_name, "errors": errors, **(data or {})},
        )

    def recovery_started(self, step_name: str, data: dict = None) -> None:
        emit(
            self.session_id,
            "RECOVERY_STARTED",
            {"step": step_name, **(data or {})},
        )

    def recovery_completed(self, step_name: str, output: dict = None) -> None:
        emit(
            self.session_id,
            "RECOVERY_COMPLETED",
            {"step": step_name, "output": output or {}},
        )

    def work_completed(self, result: dict) -> None:
        emit(self.session_id, "WORK_COMPLETED", result or {})


# Convenience: create a bus instance that the engine can use directly.
bus = EventBus  # expose as a class so ``bus = EventBus(session_id)`` works