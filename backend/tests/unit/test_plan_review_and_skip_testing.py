import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.workers.base.contract import TaskContract
from app.workers.base.engine import WorkerEngine
from app.workers.antigravity_worker.agent.worker_agent import AntigravityWorkerAgent
from app.registry.tool_registry import ToolRegistry


@pytest.mark.asyncio
async def test_plan_rejection_routes_back_to_planning(tmp_path):
    """When a plan is rejected with feedback, the worker should re-enter planning phase."""
    registry = ToolRegistry()
    contract = TaskContract(
        objective="Build a test module",
        fs_scope=str(tmp_path),
        requires_plan_approval=True,
    )

    agent = AntigravityWorkerAgent(
        objective=contract.objective,
        fs_scope=contract.fs_scope,
        requires_plan_approval=True,
    )

    engine = WorkerEngine(registry, agent_factory=lambda c: agent)
    engine.fork(contract)

    # Initial plan authored
    agent.implementation_plan = "Initial plan"
    agent._phase = "awaiting_approval"

    # User calls reject_plan with feedback
    engine.reject_plan("Please add database models first.")

    assert engine._plan_action == "rejected"
    assert engine._plan_feedback == "Please add database models first."

    # Agent rejects plan
    agent.reject_plan(engine._plan_feedback)
    assert agent._phase == "planning"
    assert agent._revision_feedback == "Please add database models first."


@pytest.mark.asyncio
async def test_plan_approval_writes_markdown_to_fs_scope(tmp_path):
    """When plan is approved with edited markdown, it must be written to {fs_scope}/implementation_plan.md."""
    registry = ToolRegistry()
    contract = TaskContract(
        objective="Build a feature",
        fs_scope=str(tmp_path),
        requires_plan_approval=True,
    )

    agent = AntigravityWorkerAgent(
        objective=contract.objective,
        fs_scope=contract.fs_scope,
        requires_plan_approval=True,
    )

    engine = WorkerEngine(registry, agent_factory=lambda c: agent)
    engine.fork(contract)

    edited_plan = "# My Custom Edited Plan\n\n- Step 1: Do something special"
    engine.approve_plan(edited_plan, skip_testing=True)

    # Verify implementation_plan.md was written to workspace disk
    plan_file = tmp_path / "implementation_plan.md"
    assert plan_file.is_file()
    assert plan_file.read_text(encoding="utf-8") == edited_plan
    assert contract.skip_testing is True
    assert engine._skip_testing is True


@pytest.mark.asyncio
async def test_skip_testing_bypasses_job_3(tmp_path):
    """When skip_testing is True, worker finishes after Job 2 without entering Job 3."""
    agent = AntigravityWorkerAgent(
        objective="Build a feature without tests",
        fs_scope=str(tmp_path),
        skip_testing=True,
    )
    agent._phase = "execution"

    with patch("app.workers.antigravity_worker.agent.worker_agent.run_antigravity_cli", new_callable=AsyncMock) as mock_cli:
        from app.workers.antigravity_worker.agent.cli_client import RunResult
        mock_cli.return_value = RunResult(success=True, output_text="Executed successfully", events=[])

        decision = await agent.decide_next_step()
        assert decision["action"] == "tool"
        assert "(Testing Skipped)" in decision["params"]["step"]
        assert agent._phase == "done"

        # Next step should be done (not testing)
        final_decision = await agent.decide_next_step()
        assert final_decision["action"] == "done"
