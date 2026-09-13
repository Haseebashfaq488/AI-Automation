"""Tests for agent memory: short-term chat memory, long-term memory, and the /agent integration."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.modules.database.db import Base
from app.modules.memory import ChatMemory, LongTermMemory
from app.modules.database import models  # noqa: F401  (register Memory on Base)
import app.api.routes.agent as agent_route


@pytest.fixture
def mem_db_factory():
    # StaticPool keeps one shared in-memory connection across threads (TestClient
    # runs the app in a worker thread).
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    yield factory
    engine.dispose()


# ---------------------------------------------------------------------------
# ChatMemory (short-term)
# ---------------------------------------------------------------------------

def test_chat_memory_add_and_history():
    mem = ChatMemory(max_messages=3)
    mem.add("s1", "user", "one")
    mem.add("s1", "assistant", "two")
    history = mem.history("s1")
    assert [m["content"] for m in history] == ["one", "two"]
    assert history[0]["role"] == "user"


def test_chat_memory_sliding_window():
    mem = ChatMemory(max_messages=3)
    for i in range(5):
        mem.add("s", "user", f"msg{i}")
    history = mem.history("s")
    assert len(history) == 3
    assert history[0]["content"] == "msg2"  # oldest within window


def test_chat_memory_sessions_isolated_and_clear():
    mem = ChatMemory()
    mem.add("a", "user", "for-a")
    mem.add("b", "user", "for-b")
    assert mem.history("a")[0]["content"] == "for-a"
    mem.clear("a")
    assert mem.history("a") == []
    assert len(mem.history("b")) == 1
    mem.clear()
    assert mem.history("b") == []


# ---------------------------------------------------------------------------
# LongTermMemory
# ---------------------------------------------------------------------------

def test_long_term_add_dedupe_and_list(mem_db_factory):
    mem = LongTermMemory(session_factory=mem_db_factory)
    assert mem.add("My downloads folder is D:/Downloads") is True
    assert mem.add("My downloads folder is D:/Downloads") is False  # duplicate
    assert mem.add("  ") is False  # empty
    assert mem.all() == ["My downloads folder is D:/Downloads"]


def test_long_term_search_and_clear(mem_db_factory):
    mem = LongTermMemory(session_factory=mem_db_factory)
    mem.add("Downloads live at D:/Downloads")
    mem.add("I prefer dark mode")
    assert mem.search("downloads") == ["Downloads live at D:/Downloads"]
    assert mem.search("missing") == []
    assert mem.clear() == 2
    assert mem.all() == []


# ---------------------------------------------------------------------------
# Agent integration with a fake adapter
# ---------------------------------------------------------------------------

class FakeAdapter:
    """Records history/memories; returns canned plans; extracts canned facts."""

    def __init__(self):
        self.calls = []

    async def analyze_prompt(self, prompt, history=None, memories=None):
        self.calls.append({"prompt": prompt, "history": list(history or []), "memories": list(memories or [])})
        if prompt == "plan please":
            return {
                "type": "plan", "reasoning": "r", "plan_id": "fakeplan1",
                "steps": [{"tool": "exists", "params": {"path": "."}, "description": "check"}],
            }
        return {"type": "response", "message": "fake reply"}

    async def extract_memories(self, prompt, outcome, max_facts=3):
        if "remember" in prompt.lower():
            return ["User's favorite folder is D:/Stuff"]
        return []

    async def close(self):
        pass


@pytest.fixture
def fake_agent_env(monkeypatch, mem_db_factory):
    fake = FakeAdapter()
    monkeypatch.setattr(agent_route, "_adapter", fake)
    monkeypatch.setattr(agent_route, "chat_memory", ChatMemory(max_messages=10))
    monkeypatch.setattr(agent_route, "long_term_memory", LongTermMemory(session_factory=mem_db_factory))
    # clear any cached plans
    agent_route._plan_cache.clear()
    return fake


def test_agent_passes_history_and_memories(client, fake_agent_env):
    fake = fake_agent_env
    client.post("/agent/run", json={"prompt": "hi there", "session_id": "s1"})
    assert len(fake.calls[0]["history"]) == 0  # first turn: no history

    client.post("/agent/run", json={"prompt": "again", "session_id": "s1"})
    second = fake.calls[1]
    # history now contains: user, assistant, user, assistant turns from turn 1
    assert len(second["history"]) == 2
    assert second["history"][0] == {"role": "user", "content": "hi there"}
    assert second["history"][1]["role"] == "assistant"

    # different session -> no shared history
    client.post("/agent/run", json={"prompt": "new session", "session_id": "s2"})
    assert len(fake.calls[2]["history"]) == 0


def test_agent_confirmed_plan_executes_and_stores_memory(client, fake_agent_env):
    r1 = client.post("/agent/run", json={"prompt": "plan please", "session_id": "s1"})
    assert r1.json()["mode"] == "plan"
    r2 = client.post("/agent/run", json={
        "prompt": "plan please", "confirm": True, "plan_id": "fakeplan1", "session_id": "s1",
    })
    body = r2.json()
    assert body["mode"] == "execution"
    assert body["success"] is True
    assert body["completed"] == 1
    # no "remember" in prompt -> nothing learned
    assert body["memories_learned"] == []


def test_agent_extracts_long_term_memory(client, fake_agent_env):
    r = client.post("/agent/run", json={"prompt": "Please remember this", "session_id": "s1"})
    assert r.json()["memories_learned"] == ["User's favorite folder is D:/Stuff"]
    # memory endpoint reflects it
    r2 = client.get("/agent/memory")
    assert "User's favorite folder is D:/Stuff" in r2.json()["memories"]


def test_agent_memory_injected_into_next_call(client, fake_agent_env):
    client.post("/agent/run", json={"prompt": "remember this please", "session_id": "s1"})
    fake = fake_agent_env
    client.post("/agent/run", json={"prompt": "later question", "session_id": "s1"})
    assert fake.calls[-1]["memories"] == ["User's favorite folder is D:/Stuff"]


def test_agent_history_endpoints(client, fake_agent_env):
    client.post("/agent/run", json={"prompt": "hello", "session_id": "hist"})
    r = client.get("/agent/history", params={"session_id": "hist"})
    assert len(r.json()["history"]) == 2
    r = client.delete("/agent/history", params={"session_id": "hist"})
    assert r.status_code == 200
    r = client.get("/agent/history", params={"session_id": "hist"})
    assert r.json()["history"] == []


def test_agent_clear_long_term_memory(client, fake_agent_env):
    client.post("/agent/run", json={"prompt": "remember this", "session_id": "s1"})
    assert len(client.get("/agent/memory").json()["memories"]) == 1
    r = client.delete("/agent/memory")
    assert r.json()["deleted"] == 1
    assert client.get("/agent/memory").json()["memories"] == []
