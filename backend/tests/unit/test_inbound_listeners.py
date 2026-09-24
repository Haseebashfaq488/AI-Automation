import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.events.bus import get_event_bus
from app.core.events.schema import EventType, JarvisEvent
from app.modules.whatsapp.helpers.listener import WhatsAppInboundListener
from app.modules.gmail.helpers.listener import GmailInboundListener


@pytest.mark.asyncio
async def test_whatsapp_inbound_listener_emits_event():
    listener = WhatsAppInboundListener(poll_interval=0.05)
    mock_client = AsyncMock()
    mock_client.status.return_value = {"state": "ready"}
    # First scan: initial state
    mock_client.list_chats.return_value = [
        {"id": "chat_1", "name": "Alice", "preview": "Hello", "unread": 0}
    ]

    bus = get_event_bus()
    emitted = []

    def on_event(evt: JarvisEvent):
        emitted.append(evt)

    bus.on(EventType.WHATSAPP_INBOUND_DIGEST, on_event)

    with patch("app.modules.whatsapp.helpers.listener.get_client", return_value=mock_client):
        listener.start()
        # Wait for initial scan
        await asyncio.sleep(0.1)

        # Update chat with new unread message
        mock_client.list_chats.return_value = [
            {"id": "chat_1", "name": "Alice", "preview": "New order confirmed!", "unread": 1}
        ]
        await asyncio.sleep(0.15)
        await listener.stop()

    assert len(emitted) >= 1
    evt = emitted[0]
    assert evt.event_type == EventType.WHATSAPP_INBOUND_DIGEST
    assert "Alice" in evt.title
    assert "New order confirmed!" in evt.summary


@pytest.mark.asyncio
async def test_gmail_inbound_listener_emits_event():
    listener = GmailInboundListener(poll_interval=0.05)
    bus = get_event_bus()
    emitted = []

    def on_event(evt: JarvisEvent):
        emitted.append(evt)

    bus.on(EventType.GMAIL_INBOUND_DIGEST, on_event)

    mock_emails_pass1 = [
        {"id": "msg_1", "from": "bob@example.com", "subject": "Old", "snippet": "Old text"}
    ]
    mock_emails_pass2 = [
        {"id": "msg_1", "from": "bob@example.com", "subject": "Old", "snippet": "Old text"},
        {"id": "msg_2", "from": "carol@example.com", "subject": "Quarterly Report", "snippet": "Attached is the Q3 report"},
    ]

    call_count = 0

    def mock_fetch(creds):
        nonlocal call_count
        call_count += 1
        return mock_emails_pass1 if call_count == 1 else mock_emails_pass2

    listener._fetch_recent_emails = mock_fetch

    with patch("app.modules.gmail.helpers.listener._load_creds", return_value=MagicMock()):
        listener.start()
        await asyncio.sleep(0.4)
        await listener.stop()


    assert len(emitted) >= 1
    evt = emitted[0]
    assert evt.event_type == EventType.GMAIL_INBOUND_DIGEST
    assert "Quarterly Report" in evt.title
    assert "carol@example.com" in evt.summary
