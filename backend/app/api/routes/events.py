import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.events.bus import get_event_bus
from app.core.events.orchestrator import get_orchestrator
from app.core.events.schema import EventType, JarvisEvent

router = APIRouter(prefix="/events", tags=["events"])
logger = logging.getLogger("jarvis.events.routes")


class HookRegistrationRequest(BaseModel):
    target_session_id: str
    action_tool: str
    action_params: Dict[str, Any] = {}
    description: str = ""


class ManualEventRequest(BaseModel):
    event_type: EventType
    title: str
    summary: str
    source: str = "manual"
    data: Dict[str, Any] = {}


@router.get("/recent")
async def get_recent_events(limit: int = Query(30, ge=1, le=100)) -> List[Dict[str, Any]]:
    """Return recently buffered events for instant UI loading."""
    bus = get_event_bus()
    events = bus.get_history(limit=limit)
    return [e.model_dump() for e in events]


@router.post("/hook")
async def register_task_hook(request: HookRegistrationRequest) -> Dict[str, Any]:
    """Register a reactive follow-up action to execute when target_session_id completes."""
    orchestrator = get_orchestrator()
    hook = orchestrator.register_hook(
        target_session_id=request.target_session_id,
        action_tool=request.action_tool,
        action_params=request.action_params,
        description=request.description,
    )
    return {"status": "registered", "hook": hook.model_dump()}


@router.post("/publish")
async def publish_manual_event(request: ManualEventRequest) -> Dict[str, Any]:
    """Manually publish an event to the global event bus."""
    bus = get_event_bus()
    event = JarvisEvent(
        event_type=request.event_type,
        source=request.source,
        title=request.title,
        summary=request.summary,
        data=request.data,
    )
    bus.publish(event)
    return {"status": "published", "event": event.model_dump()}


@router.get("/stream")
async def stream_events(request: Request):
    """Multi-subscriber Server-Sent Events (SSE) stream."""
    bus = get_event_bus()
    queue = bus.subscribe_sse()

    async def event_generator():
        try:
            # 1. First replay recent events to bootstrap client state
            recent_events = bus.get_history(limit=20)
            for rev in recent_events:
                yield f"data: {rev.to_sse_payload()}\n\n"

            # 2. Stream live events
            while True:
                if await request.is_disconnected():
                    break

                try:
                    # Wait for next event or keep-alive ping
                    event: JarvisEvent = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {event.to_sse_payload()}\n\n"
                except asyncio.TimeoutError:
                    # SSE keepalive comment
                    yield ": ping\n\n"

        except asyncio.CancelledError:
            pass
        finally:
            bus.unsubscribe_sse(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
