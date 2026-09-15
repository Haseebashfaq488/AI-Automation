import asyncio
import os

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.api.routes import workers as workers_routes
from app.api.routes.agent import _execute_plan, _fork_task
from app.workers.base.session import WorkerSession


@pytest.fixture(autouse=True)
def isolated_sessions(tmp_path, monkeypatch):
    monkeypatch.setattr(WorkerSession, "SESSIONS_ROOT", tmp_path / "sessions")
    # Deterministic placeholder mode — hide the opencode binary so the
    # OpenCodeWorkerAgent reports available=False and the engine falls
    # back to its deterministic placeholder loop.
    monkeypatch.setattr(
        "app.workers.opencode_worker.agent.config.get_opencode_binary", lambda: None
    )
    workers_routes._engines.clear()
    yield
    workers_routes._engines.clear()


async def _wait_terminal(session_id: str, timeout=10):
    eng = workers_routes._engines[session_id]
    async def poll():
        while True:
            state = eng.get_state()
            if state["status"] in ("completed", "cancelled"):
                return state
            await asyncio.sleep(0.05)
    await asyncio.wait_for(poll(), timeout)


# ── fork tool (agent plan interception) ─────────────────────────────────


@pytest.mark.asyncio
async def test_fork_task_creates_queryable_worker(tmp_path):
    result = await _fork_task(
        {"objective": "Normalize headings", "fs_scope": str(tmp_path)},
        prompt="fork the task: normalize headings",
    )
    assert result["success"] is True
    data = result["data"]
    assert data["session_id"] in workers_routes._engines
    assert data["worker_url"] == f"/worker/{data['session_id']}"

    await _wait_terminal(data["session_id"])
    state = workers_routes.get_engine(data["session_id"]).get_state()
    assert state["status"] == "completed"


@pytest.mark.asyncio
async def test_fork_task_defaults_objective_to_prompt(tmp_path):
    result = await _fork_task({}, prompt="fork the task")
    assert result["success"] is True
    eng = workers_routes.get_engine(result["data"]["session_id"])
    assert eng._contract.objective == "fork the task"
    # default coding toolset applied
    assert "list_directory" in eng._contract.allowed_tools


@pytest.mark.asyncio
async def test_execute_plan_intercepts_fork_before_engine(tmp_path):
    steps = [
        {"tool": "fork", "params": {"objective": "Fix report", "fs_scope": str(tmp_path)}},
        # A normal registry tool still executes afterwards.
        {"tool": "list_directory", "params": {"path": str(tmp_path)}},
    ]
    outcome = await _execute_plan(steps, prompt="fork the task: fix report")
    assert outcome["success"] is True
    assert outcome["total_steps"] == 2

    fork_step = outcome["results"][0]
    assert fork_step["tool"] == "fork"
    assert fork_step["success"] is True
    assert fork_step["data"]["worker_url"].startswith("/worker/")

    list_step = outcome["results"][1]
    assert list_step["tool"] == "list_directory"
    assert list_step["success"] is True


# ── plan validation: fork survives with no params ───────────────────────


def test_adapter_accepts_bare_fork_step():
    from app.modules.opencode.adapter import OpenCodeAdapter

    adapter = OpenCodeAdapter.__new__(OpenCodeAdapter)  # no API key needed
    adapter.registry = None
    valid, dropped = adapter._validate_plan_steps(
        [{"tool": "fork", "params": {}, "description": "Fork a worker"}]
    )
    assert dropped == []
    assert len(valid) == 1
    assert valid[0]["tool"] == "fork"


# ── sessions survive backend restart (disk fallback) ────────────────────


@pytest.mark.asyncio
async def test_worker_endpoints_fall_back_to_disk(tmp_path):
    # Fork + finish a worker, then simulate a restart by dropping the engine.
    result = await _fork_task({"objective": "disk persistence check", "fs_scope": str(tmp_path)}, "")
    session_id = result["data"]["session_id"]
    await _wait_terminal(session_id)
    workers_routes._engines.clear()  # ← backend "restarted"

    app = create_app()
    with TestClient(app) as client:
        resp = client.get(f"/workers/{session_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

        resp = client.get(f"/workers/{session_id}/result")
        assert resp.status_code == 200
        # The persisted result round‑trips (the placeholder worker's own
        # success/failure is irrelevant to the persistence check).
        assert "success" in resp.json()["result"]

        resp = client.get("/workers/list")
        ids = [w["session_id"] for w in resp.json()["workers"]]
        assert session_id in ids


def test_unknown_worker_still_404s(tmp_path):
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/workers/ws_doesnotexist")
        assert resp.status_code == 404
