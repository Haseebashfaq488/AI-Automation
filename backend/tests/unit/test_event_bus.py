import asyncio
import pytest
from app.core.events.bus import GlobalEventBus
from app.core.events.schema import EventType, JarvisEvent


@pytest.mark.asyncio
async def test_event_bus_publish_and_history():
    bus = GlobalEventBus(history_size=10)
    event1 = JarvisEvent(
        event_type=EventType.WHATSAPP_INBOUND_DIGEST,
        source="test",
        title="WhatsApp Test",
        summary="Test message",
    )
    bus.publish(event1)

    history = bus.get_history()
    assert len(history) == 1
    assert history[0].id == event1.id
    assert history[0].title == "WhatsApp Test"


@pytest.mark.asyncio
async def test_event_bus_topic_listeners():
    bus = GlobalEventBus(history_size=10)
    received = []

    def on_worker_completed(evt: JarvisEvent):
        received.append(evt)

    bus.on(EventType.WORKER_COMPLETED, on_worker_completed)

    # Publish unrelated event
    bus.publish(
        JarvisEvent(
            event_type=EventType.WHATSAPP_INBOUND_DIGEST,
            source="test",
            title="Unrelated",
            summary="Ignored",
        )
    )
    assert len(received) == 0

    # Publish matched event
    worker_evt = JarvisEvent(
        event_type=EventType.WORKER_COMPLETED,
        source="worker:test_1",
        title="Worker Finished",
        summary="Done",
        data={"session_id": "test_1"},
    )
    bus.publish(worker_evt)
    assert len(received) == 1
    assert received[0].data["session_id"] == "test_1"


@pytest.mark.asyncio
async def test_event_bus_sse_subscription():
    bus = GlobalEventBus(history_size=10)
    q = bus.subscribe_sse()

    evt = JarvisEvent(
        event_type=EventType.GMAIL_INBOUND_DIGEST,
        source="gmail:test",
        title="Email Received",
        summary="Test email",
    )
    bus.publish(evt)

    assert not q.empty()
    item = q.get_nowait()
    assert item.id == evt.id
    assert item.title == "Email Received"

    bus.unsubscribe_sse(q)
    # Publishing again should not push to unsubscribed queue
    bus.publish(evt)
    assert q.empty()
