import asyncio
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.registry import registry
from app.workers.base.bus import EventBus
from app.workers.base.contract import TaskContract
from app.workers.base.engine import WorkerEngine
from app.workers.base.scoped_registry import ScopedToolRegistry
from app.workers.base.session import WorkerSession


import os

from pydantic import ValidationError

from app.workers.base.bus import EventBus
from app.workers.base.contract import TaskContract
from app.workers.base.engine import WorkerEngine
from app.workers.base.scoped_registry import ScopedToolRegistry
from app.workers.base.session import WorkerSession

# Platform-independent absolute path for contract fixtures
SCOPE = os.path.abspath("/tmp")


def _contract(**overrides) -> TaskContract:
    base = dict(
        objective="Test objective",
        requirements=["req1"],
        constraints=["don't break things"],
        success_criteria=["it works"],
        fs_scope=SCOPE,
        allowed_tools=["create_file", "exists"],
        max_steps=10,
    )
    base.update(overrides)
    return TaskContract(**base)


# ── TaskContract ────────────────────────────────────────────────────────


class TestTaskContract:
    def test_valid_contract(self):
        c = _contract()
        assert c.objective == "Test objective"
        assert c.max_steps == 10

    def test_fs_scope_must_be_absolute(self):
        with pytest.raises(ValidationError):
            _contract(fs_scope="relative/path")

    def test_roundtrip_json(self):
        c = _contract()
        restored = TaskContract.model_validate_json(c.model_dump_json())
        assert restored.objective == c.objective
        assert restored.allowed_tools == c.allowed_tools

    def test_defaults(self):
        c = TaskContract(objective="x", fs_scope=SCOPE)
        assert c.requirements == []
        assert c.allowed_tools == []
        assert c.max_steps == 20
        assert c.timeout_seconds is None


# ── WorkerSession ───────────────────────────────────────────────────────


class TestWorkerSession:
    def test_fork_creates_session_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(WorkerSession, "SESSIONS_ROOT", tmp_path)
        session = WorkerSession("ws_test1", _contract()).fork()

        assert (session.path / "task.json").is_file()
        assert (session.path / "state.json").is_file()
        assert (session.path / "events.jsonl").is_file()
        assert (session.path / "artifacts").is_dir()
        assert (session.path / "result.json").is_file()

        state = session.read_state()
        assert state["completed"] == []
        assert state["remaining"] == ["Test objective"]

        task = session.read_task()
        assert task.objective == "Test objective"

    def test_append_and_state_updates(self, tmp_path, monkeypatch):
        monkeypatch.setattr(WorkerSession, "SESSIONS_ROOT", tmp_path)
        session = WorkerSession("ws_test2", _contract()).fork()

        session.append_event("STEP_COMPLETED", {"step": "create_file", "index": 0})
        lines = (session.path / "events.jsonl").read_text().strip().splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0])["type"] == "STEP_COMPLETED"

        session.write_state({"completed": ["create_file"], "remaining": [], "errors": [], "progress_percent": 100, "current_step": None})
        assert session.completed == ["create_file"]
        assert session.progress_percent == 100

        session.write_result({"success": True})
        assert session.read_result()["success"] is True


# ── ScopedToolRegistry ──────────────────────────────────────────────────


class TestScopedRegistry:
    def test_only_allowed_tools_visible(self):
        scoped = ScopedToolRegistry(registry, {"read_file", "exists"})
        tools = scoped.list_tools()
        assert set(tools.keys()) == {"read_file", "exists"}

    def test_get_blocked_tool_raises(self):
        scoped = ScopedToolRegistry(registry, {"read_file"})
        with pytest.raises(KeyError):
            scoped.get("delete_file")

    def test_allowed_tool_returns_instance(self):
        scoped = ScopedToolRegistry(registry, {"read_file"})
        assert scoped.get("read_file").name == "read_file"

    def test_contains(self):
        scoped = ScopedToolRegistry(registry, {"read_file"})
        assert "read_file" in scoped
        assert "delete_file" not in scoped


# ── EventBus ────────────────────────────────────────────────────────────


class TestEventBus:
    def test_events_reach_subscribers(self):
        received = []
        from app.workers.base import bus as bus_mod

        bus_mod.on("ws_events_test", lambda t, d: received.append((t, d)))
        ev = EventBus("ws_events_test")
        ev.work_started({"objective": "x"})
        ev.step_started("create_file", 0)
        ev.work_completed({"success": True})

        types = [t for t, _ in received]
        assert types == ["WORK_STARTED", "STEP_STARTED", "WORK_COMPLETED"]
        # cleanup global registry for other tests
        bus_mod._bus.pop("ws_events_test", None)


# ── WorkerEngine (end‑to‑end, no LLM) ───────────────────────────────────


class TestWorkerEngine:
    @pytest.mark.asyncio
    async def test_run_completes_and_writes_result(self, tmp_path, monkeypatch):
        monkeypatch.setattr(WorkerSession, "SESSIONS_ROOT", tmp_path)
        eng = WorkerEngine(registry, session_id="ws_e2e")
        state = await eng.run(_contract())
        assert state["status"] == "running"

        for _ in range(100):
            await asyncio.sleep(0.05)
            if eng.get_state()["status"] != "running":
                break

        final = eng.get_state()
        assert final["status"] == "completed"
        assert final["progress_percent"] == 100
        assert set(final["completed"]) == {"create_file", "exists"}

        result = eng.get_result()
        assert result["success"] is True
        assert result["cancelled"] is False
        assert len(result["errors"]) == 0

        # Session files were persisted
        session_dir = tmp_path / "ws_e2e"
        assert (session_dir / "result.json").is_file()
        events = (session_dir / "events.jsonl").read_text()
        assert "WORK_STARTED" in events
        assert "WORK_COMPLETED" in events

    @pytest.mark.asyncio
    async def test_scoped_registry_enforced_in_loop(self, tmp_path, monkeypatch):
        """The worker must not be able to call tools outside allowed_tools."""
        monkeypatch.setattr(WorkerSession, "SESSIONS_ROOT", tmp_path)
        # 'not_a_real_tool' will fail validation; 'delete_file' is NOT in the
        # allowed list, so the engine must never reach it even if requested.
        eng = WorkerEngine(registry, session_id="ws_scoped")
        contract = _contract(allowed_tools=["create_file"])
        await eng.run(contract)

        for _ in range(100):
            await asyncio.sleep(0.05)
            if eng.get_state()["status"] != "running":
                break

        result = eng.get_result()
        assert result["tools_used"] == ["create_file"]
        assert all(e["tool"] != "delete_file" for e in result["errors"])

    @pytest.mark.asyncio
    async def test_cancel_stops_worker(self, tmp_path, monkeypatch):
        monkeypatch.setattr(WorkerSession, "SESSIONS_ROOT", tmp_path)
        eng = WorkerEngine(registry, session_id="ws_cancel")
        await eng.run(_contract(allowed_tools=["create_file", "exists", "write_file", "touch"]))
        eng.cancel()

        for _ in range(100):
            await asyncio.sleep(0.05)
            status = eng.get_state()["status"]
            if status in ("completed", "cancelled"):
                break

        assert eng.get_state()["status"] in ("cancelled", "completed")
        assert eng.get_result().get("cancelled") is True

    @pytest.mark.asyncio
    async def test_intervention_recorded(self, tmp_path, monkeypatch):
        monkeypatch.setattr(WorkerSession, "SESSIONS_ROOT", tmp_path)
        eng = WorkerEngine(registry, session_id="ws_intervene")
        eng.intervene("Try a different approach")
        await eng.run(_contract())

        for _ in range(100):
            await asyncio.sleep(0.05)
            if eng.get_state()["status"] != "running":
                break

        events = (tmp_path / "ws_intervene" / "events.jsonl").read_text()
        assert "PARENT_INTERVENTION" in events
