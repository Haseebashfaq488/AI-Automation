import asyncio
import json
import pytest
from pathlib import Path

from app.workers.base.contract import TaskContract
from app.workers.base.session import WorkerSession
from app.workers.base.engine import WorkerEngine
from app.registry import registry
from app.workers.antigravity_worker.agent.milestones import (
    build_planning_prompt,
    build_execution_prompt,
    build_master_task_prompt,
    _format_handover_section,
    _living_docs_section,
)
from app.api.routes import workers as workers_routes


@pytest.fixture(autouse=True)
def isolated_sessions(tmp_path, monkeypatch):
    monkeypatch.setattr(WorkerSession, "SESSIONS_ROOT", tmp_path / "sessions")
    # Deterministic placeholder mode — hide binaries so agents report
    # available=False and the engine falls back to deterministic loop.
    monkeypatch.setattr(
        "app.workers.opencode_worker.agent.config.get_opencode_binary", lambda: None
    )
    monkeypatch.setattr(
        "app.workers.antigravity_worker.agent.config.get_agy_binary", lambda: None
    )
    workers_routes._engines.clear()
    yield
    workers_routes._engines.clear()


async def _wait_terminal(session_id: str, timeout=5):
    eng = workers_routes._engines.get(session_id)
    if not eng:
        return
    async def poll():
        while True:
            state = eng.get_state()
            if state["status"] in ("completed", "cancelled", "failed"):
                return state
            await asyncio.sleep(0.05)
    await asyncio.wait_for(poll(), timeout)


def test_contract_handover_fields(tmp_path: Path):
    """Test that TaskContract properly validates and retains handover fields."""
    contract = TaskContract(
        objective="Refine landing page hero",
        fs_scope=str(tmp_path),
        prior_handover={"objective": "Build initial landing page", "status": "completed"},
        is_refinement=True,
        folder_manifests=["components/README.md", "styles/README.md"],
    )
    assert contract.is_refinement is True
    assert contract.prior_handover["objective"] == "Build initial landing page"
    assert "components/README.md" in contract.folder_manifests


def test_session_handover_io(tmp_path: Path):
    """Test WorkerSession write_handover and read_handover."""
    session = WorkerSession("test_session_123")

    data = {
        "session_id": "test_session_123",
        "objective": "Build component",
        "status": "completed",
        "artifacts": ["index.html"],
    }
    session.write_handover(data)

    read_back = session.read_handover()
    assert read_back["session_id"] == "test_session_123"
    assert read_back["status"] == "completed"
    assert read_back["artifacts"] == ["index.html"]


def test_engine_synthesize_handover(tmp_path: Path):
    """Test WorkerEngine._synthesize_handover creates SESSION_HANDOVER.md and handover.json."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    comp_dir = workspace / "components"
    comp_dir.mkdir()
    (comp_dir / "README.md").write_text("# Components\nUI components living documentation", encoding="utf-8")
    styles_dir = workspace / "styles"
    styles_dir.mkdir()
    (styles_dir / "README.md").write_text("# Styles\nCSS design tokens", encoding="utf-8")

    contract = TaskContract(
        objective="Build modular landing page",
        fs_scope=str(workspace),
    )

    engine = WorkerEngine(registry)
    engine.fork(contract)

    result_data = {
        "success": True,
        "artifacts": [str(workspace / "index.html")],
        "summary": "Completed landing page implementation",
        "test_results": {"passed": 3, "failed": 0},
        "implementation_plan": "- Adopt Vanilla CSS and custom tokens\n- Structure components modularly",
    }

    handover = engine._synthesize_handover(result_data)
    assert handover["status"] == "completed"
    assert len(handover["folder_manifests"]) >= 2
    assert any("components" in m for m in handover["folder_manifests"])
    assert any("styles" in m for m in handover["folder_manifests"])

    # Check files written in workspace
    assert (workspace / "handover.json").is_file()
    assert (workspace / "SESSION_HANDOVER.md").is_file()
    handover_md = (workspace / "SESSION_HANDOVER.md").read_text(encoding="utf-8")
    assert "Project Handover Brief" in handover_md
    assert "Build modular landing page" in handover_md
    assert "components/README.md" in handover_md or "components\\README.md" in handover_md


@pytest.mark.asyncio
async def test_launch_worker_autodetects_handover(tmp_path: Path):
    """Test launch_worker automatically detects existing handover in workspace."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    existing_handover = {
        "session_id": "session_prior",
        "objective": "Build initial site",
        "status": "completed",
        "architecture_decisions": ["Used pure CSS"],
    }
    (workspace / "handover.json").write_text(json.dumps(existing_handover), encoding="utf-8")

    contract = TaskContract(
        objective="Update hero banner",
        fs_scope=str(workspace),
    )

    state = await workers_routes.launch_worker(contract, worker_type="opencode_worker")
    assert contract.is_refinement is True
    assert contract.prior_handover is not None
    assert contract.prior_handover["objective"] == "Build initial site"

    await _wait_terminal(state["session_id"])


def test_milestone_prompt_builders_incorporate_handover():
    """Test that prompt builders in milestones.py embed living docs and handover instructions."""
    living_docs = _living_docs_section()
    assert "Living Documentation Protocol" in living_docs
    assert "README.md" in living_docs

    handover = {
        "objective": "Build portfolio",
        "status": "completed",
        "architecture_decisions": ["Used glassmorphism tokens"],
    }
    handover_section = _format_handover_section(handover, ["components/README.md"], is_refinement=True)
    assert "SESSION CONTINUATION & PRIOR HANDOVER" in handover_section
    assert "Build portfolio" in handover_section
    assert "glassmorphism tokens" in handover_section
    assert "NON-DESTRUCTIVE REFINEMENT RULES" in handover_section

    # Test build_planning_prompt
    plan_prompt = build_planning_prompt(
        objective="Tweak hero",
        fs_scope="D:/workspace",
        prior_handover=handover,
        folder_manifests=["components/README.md"],
        is_refinement=True,
    )
    assert "SESSION CONTINUATION & PRIOR HANDOVER" in plan_prompt
    assert "Living Documentation Protocol" in plan_prompt

    # Test build_execution_prompt
    exec_prompt = build_execution_prompt(
        objective="Tweak hero",
        fs_scope="D:/workspace",
        approved_plan="1. Change color",
        prior_handover=handover,
        folder_manifests=["components/README.md"],
        is_refinement=True,
    )
    assert "SESSION CONTINUATION & PRIOR HANDOVER" in exec_prompt
    assert "Living Documentation Protocol" in exec_prompt


def test_graphify_handover_integration():
    """Test that graphify knowledge graph is signaled in handover section and contract."""
    contract = TaskContract(
        objective="Analyze project",
        fs_scope="D:/workspace",
        has_graphify=True,
    )
    assert contract.has_graphify is True

    handover_with_graph = {
        "objective": "Build app",
        "has_graphify": True,
        "architecture_decisions": ["Used FastAPI"],
    }
    rendered = _format_handover_section(handover_with_graph, ["src/README.md"], is_refinement=True)
    assert "Knowledge Graph (graphify)" in rendered
    assert "graphify query" in rendered
    assert "graphify path" in rendered


@pytest.mark.asyncio
async def test_dynamic_fs_scope_resolution(tmp_path: Path):
    """Test that _fork_task respects explicit fs_scope or extracts directory from prompt."""
    from app.api.routes.agent import _fork_task

    target_dir = tmp_path / "custom_project"
    res = await _fork_task(
        {"objective": "Create site", "fs_scope": str(target_dir)},
        prompt="build a site",
    )
    assert res["success"] is True
    assert target_dir.is_dir()

    # Test path extracted from prompt
    prompt_dir = tmp_path / "prompt_project"
    res2 = await _fork_task(
        {"objective": "Create site"},
        prompt=f"build a landing page in {prompt_dir}",
    )
    assert res2["success"] is True
    assert prompt_dir.is_dir()


@pytest.mark.asyncio
async def test_get_worker_handover_endpoint(tmp_path: Path):
    """Test the GET /workers/{session_id}/handover API endpoint."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.workers.base.session import WorkerSession

    session_id = "test-handover-api-session"
    session_dir = WorkerSession.SESSIONS_ROOT / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    try:
        (session_dir / "task.json").write_text(json.dumps({"objective": "Test API", "fs_scope": str(tmp_path)}), encoding="utf-8")
        handover_data = {
            "session_id": session_id,
            "objective": "Test API",
            "has_graphify": True,
            "folder_manifests": ["src/README.md"],
        }
        (session_dir / "handover.json").write_text(json.dumps(handover_data), encoding="utf-8")
        (session_dir / "SESSION_HANDOVER.md").write_text("# Session Handover Brief\n\nAll tasks completed.", encoding="utf-8")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get(f"/workers/{session_id}/handover")
            assert res.status_code == 200
            body = res.json()
            assert body["has_handover"] is True
            assert body["has_graphify"] is True
            assert body["handover"]["objective"] == "Test API"
            assert "Session Handover Brief" in body["markdown"]
            assert body["folder_manifests"] == ["src/README.md"]
    finally:
        import shutil
        if session_dir.exists():
            shutil.rmtree(session_dir, ignore_errors=True)


