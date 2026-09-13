import asyncio
import json
import threading
from collections.abc import Callable, Coroutine
from typing import Dict, List, Optional

# Global in‑process bus: session_id → list of callbacks (async or sync)
_bus: Dict[str, List[Callable]] = {}
_bus_lock = threading.Lock()


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