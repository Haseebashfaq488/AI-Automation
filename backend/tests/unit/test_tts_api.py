"""Unit tests for Edge TTS streaming endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_tts_voices_list(client):
    res = client.get("/agent/tts/voices")
    assert res.status_code == 200
    data = res.json()
    assert "voices" in data
    assert len(data["voices"]) >= 5
    assert data["default"] == "en-US-AvaNeural"


def test_clean_text_strips_delimiters():
    from app.api.routes.tts import clean_text_for_speech
    raw = "<<<gesture: waving, expression: happy_wave>>> Hey Dum Dum! 🫧 <<<gesture: cheering>>> Great to see you!"
    cleaned = clean_text_for_speech(raw)
    assert "<<<" not in cleaned
    assert "gesture:" not in cleaned
    assert "Hey Dum Dum!" in cleaned
    assert "Great to see you!" in cleaned


def test_tts_empty_text_returns_400(client):
    res = client.post("/agent/tts", json={"text": "<<<gesture: waving>>>   "})
    assert res.status_code == 400
    assert "speakable content" in res.json()["detail"]
