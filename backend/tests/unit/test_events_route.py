import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.events.bus import get_event_bus
from app.core.events.schema import EventType, JarvisEvent


@pytest.fixture
def client():
    return TestClient(app)


def test_events_recent_endpoint(client):
    bus = get_event_bus()
    bus.publish(
        JarvisEvent(
            event_type=EventType.SYSTEM_NOTIFICATION,
            source="test",
            title="System Ready",
            summary="All systems nominal",
        )
    )

    response = client.get("/events/recent?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(e["title"] == "System Ready" for e in data)


def test_events_publish_endpoint(client):
    payload = {
        "event_type": "WHATSAPP_INBOUND_DIGEST",
        "title": "WhatsApp: John Doe",
        "summary": "[09:30 AM] John Doe: Hey are we meeting today?",
        "source": "manual",
        "data": {"unread": 1},
    }
    response = client.post("/events/publish", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "published"


def test_events_hook_endpoint(client):
    payload = {
        "target_session_id": "ws_api_test_session",
        "action_tool": "send_message",
        "action_params": {"to": "+923098956995", "message": "Done"},
        "description": "Notify on WhatsApp",
    }
    response = client.post("/events/hook", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "registered"
