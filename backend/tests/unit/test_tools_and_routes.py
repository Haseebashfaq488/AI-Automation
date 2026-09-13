"""Regression tests for tool fixes and API routes."""
import pytest
from fastapi.testclient import TestClient

from app.core.execution_engine import ExecutionEngine
from app.registry import registry
from app.modules.opencode.adapter import OpenCodeAdapter


@pytest.fixture
def engine():
    return ExecutionEngine(registry)


# ---------------------------------------------------------------------------
# Adapter plan validation
# ---------------------------------------------------------------------------

def test_adapter_accepts_valid_plan_steps():
    adapter = OpenCodeAdapter.__new__(OpenCodeAdapter)  # skip network init
    adapter.registry = registry
    steps = [
        {"tool": "search_files", "params": {"path": "/tmp", "pattern": "*.txt"}, "description": "d"},
        {"tool": "rename", "params": {"source": "/tmp/a", "destination": "/tmp/b"}, "description": "d"},
        {"tool": "organize_downloads", "params": {"source_dir": "/tmp"}, "description": "d"},
    ]
    valid, dropped = adapter._validate_plan_steps(steps)
    assert len(valid) == 3
    assert dropped == []


def test_adapter_rejects_bad_plan_steps():
    adapter = OpenCodeAdapter.__new__(OpenCodeAdapter)  # skip network init
    adapter.registry = registry
    steps = [
        # wrong param name (legacy 'query')
        {"tool": "search_files", "params": {"path": "/tmp", "query": "x"}},
        # legacy rename params
        {"tool": "rename", "params": {"path": "/tmp/a", "new_name": "b"}},
        # legacy organize_downloads param
        {"tool": "organize_downloads", "params": {"directory": "/tmp"}},
        # unknown tool
        {"tool": "delete_everything", "params": {}},
        # missing required param
        {"tool": "write_file", "params": {"path": "/tmp/a"}},
        # not a dict
        "garbage",
    ]
    valid, dropped = adapter._validate_plan_steps(steps)
    assert valid == []
    assert len(dropped) == 5  # the "garbage" string is not a step at all


# ---------------------------------------------------------------------------
# Protected paths
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mutation_tool_rejects_protected_path(engine):
    result = await engine.run("create_folder", {"path": "C:/Windows/jarvis_test_should_fail"})
    assert result.success is False
    assert "protected" in result.error["message"].lower()


@pytest.mark.asyncio
async def test_rename_over_existing_destination(engine, tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("data")
    dst = tmp_path / "dst.txt"
    dst.write_text("old")
    result = await engine.run("rename", {"source": str(src), "destination": str(dst)})
    assert result.success is True
    assert not src.exists()
    assert dst.read_text() == "data"


# ---------------------------------------------------------------------------
# HTTP routes
# ---------------------------------------------------------------------------

def test_tools_list_contains_category(client: TestClient):
    resp = client.get("/tools/list")
    assert resp.status_code == 200
    names = {t["name"]: t for t in resp.json()["tools"]}
    assert names["read_file"]["category"] == "tool"
    assert names["organize_downloads"]["category"] == "skill"


def test_skills_list_only_skills(client: TestClient):
    resp = client.get("/skills/list")
    assert resp.status_code == 200
    skills = {s["name"] for s in resp.json()["skills"]}
    assert skills == {"organize_downloads", "send_report", "unread_digest", "list_recent_emails"}


def test_pipelines_list_and_404(client: TestClient):
    resp = client.get("/pipelines/list")
    assert resp.status_code == 200
    assert "organize_downloads" in resp.json()["pipelines"]
    resp = client.post("/pipelines/run/does_not_exist", json={})
    assert resp.status_code == 404


def test_tasks_crud(client: TestClient):
    resp = client.post("/tasks/create", json={"name": "pytest task"})
    assert resp.status_code == 200
    task_id = resp.json()["id"]
    resp = client.get(f"/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"
    resp = client.patch(f"/tasks/{task_id}", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


def test_agent_validation_errors(client: TestClient):
    # confirm without plan_id
    resp = client.post("/agent/run", json={"prompt": "x", "confirm": True})
    assert resp.status_code == 400
    # confirm with unknown plan_id
    resp = client.post("/agent/run", json={"prompt": "x", "confirm": True, "plan_id": "nope"})
    assert resp.status_code == 404
