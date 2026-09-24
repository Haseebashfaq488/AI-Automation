import pytest
from datetime import datetime, UTC, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.modules.database.db import SessionLocal
from app.modules.database.repository import Repository
from app.modules.memory.service_memory import ServiceMemoryManager, get_service_memory_manager


@pytest.fixture
def repo():
    db = SessionLocal()
    try:
        yield Repository(db)
    finally:
        db.close()


def test_service_event_crud_and_unread(repo):
    # Upsert whatsapp event
    repo.upsert_service_event(
        event_id="wa_test_1",
        service="whatsapp",
        sender="Test User",
        subject_or_title="Test Chat",
        snippet="Hello there",
        is_unread=True,
    )

    # Upsert gmail event
    repo.upsert_service_event(
        event_id="gmail_test_1",
        service="gmail",
        sender="bob@example.com",
        subject_or_title="Quarterly Review",
        snippet="Please see attached review",
        is_unread=True,
    )

    # Upsert drive event
    repo.upsert_service_event(
        event_id="drive_test_1",
        service="drive",
        sender="Haseeb",
        subject_or_title="Specs.docx",
        snippet="File modified",
        is_unread=False,
    )

    events = repo.list_service_events(hours=24)
    assert len(events) >= 3

    unreads = repo.list_service_events(unread_only=True)
    assert any(e.id == "wa_test_1" for e in unreads)
    assert any(e.id == "gmail_test_1" for e in unreads)
    assert not any(e.id == "drive_test_1" for e in unreads)

    counts = repo.get_service_unread_counts(hours=24)
    assert counts["whatsapp"] >= 1
    assert counts["gmail"] >= 1


def test_daily_digest_and_7day_retention(repo):
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    repo.upsert_daily_digest(
        day_date=today,
        service="whatsapp",
        summary_text="Discussed project architecture with Team",
        key_contacts=["Team Lead", "Ali"],
        action_items=["Finish unit tests"],
        key_topics=["Architecture", "Testing"],
    )

    digests = repo.list_daily_digests(days=7)
    assert len(digests) >= 1
    found = next((d for d in digests if d.day_date == today and d.service == "whatsapp"), None)
    assert found is not None
    assert "Discussed project architecture" in found.summary_text


def test_service_memory_manager_prompt_builder():
    mem_mgr = get_service_memory_manager()
    prompt = mem_mgr.build_brain_context_prompt()
    assert "AMBIENT MULTI-SERVICE MEMORY" in prompt
    assert "WhatsApp" in prompt
    assert "Gmail" in prompt
    assert "Drive" in prompt


def test_events_feed_and_digest_routes():
    client = TestClient(app)

    # 1. Test /events/feed
    res = client.get("/events/feed?hours=24")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 2. Test /events/unread-counts
    res_unread = client.get("/events/unread-counts")
    assert res_unread.status_code == 200
    data = res_unread.json()
    assert "whatsapp" in data
    assert "gmail" in data
    assert "drive" in data

    # 3. Test /events/7day-digests
    res_digests = client.get("/events/7day-digests?days=7")
    assert res_digests.status_code == 200
    assert isinstance(res_digests.json(), list)
