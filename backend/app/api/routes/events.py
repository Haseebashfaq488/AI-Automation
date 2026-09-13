import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/events", tags=["events"])

async def event_generator():
    counter = 0
    while True:
        await asyncio.sleep(1)
        counter += 1
        yield f"data: event {counter}\n\n"

@router.get("/stream")
async def stream_events():
    return StreamingResponse(event_generator(), media_type="text/event-stream")
