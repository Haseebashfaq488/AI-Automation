"""Unit tests for the Antigravity Autonomous Worker (Pure CLI Mode)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.workers.antigravity_worker.agent import config
from app.workers.antigravity_worker.agent.cli_client import RunResult, run_antigravity_cli
from app.workers.antigravity_worker.agent.milestones import (
    Milestone,
    MilestonePhase,
    build_prompt,
    is_simple_task,
    plan_milestones,
)
from app.workers.antigravity_worker.agent.worker_agent import AntigravityWorkerAgent
from app.workers.base.contract import TaskContract
from app.workers.base.engine import WorkerEngine
from app.registry import registry


class TestAntigravityConfig:
    def test_get_antigravity_model_override(self):
        assert config.get_antigravity_model("gemini-3.8-flash-high") == "gemini-3.8-flash-high"

    def test_get_auto_approve(self):
        assert config.get_auto_approve() is True

    def test_get_milestone_timeout(self):
        assert config.get_milestone_timeout() > 0

    def test_get_agy_binary_override(self, monkeypatch, tmp_path: Path):
        fake_bin = tmp_path / "agy.exe"
        fake_bin.write_text("echo fake agy")
        monkeypatch.setenv("ANTIGRAVITY_BIN", str(fake_bin))
        assert config.get_agy_binary() == str(fake_bin)


class TestAntigravityMilestones:
    def test_is_simple_task(self):
        assert is_simple_task("Create a file in local disk D and write lorem ipsum") is True
        assert is_simple_task("write file text.txt") is True
        assert is_simple_task("Refactor authentication pipeline across all models and write full stack tests") is False

    def test_plan_milestones_simple_task(self):
        ms = plan_milestones("Create a file hello.txt")
        assert len(ms) == 2
        assert ms[0].phase == MilestonePhase.STEP
        assert ms[1].phase == MilestonePhase.TEST

    def test_plan_milestones_complex_task(self):
        ms = plan_milestones("Refactor architecture and build full stack database integration")
        assert len(ms) == 3
        assert ms[0].phase == MilestonePhase.STEP
        assert ms[1].phase == MilestonePhase.STEP
        assert ms[2].phase == MilestonePhase.TEST

    def test_build_prompt_includes_intervention_at_top(self):
        m = Milestone(phase=MilestonePhase.STEP, title="Step 1", instructions="Do step 1")
        prompt = build_prompt(m, fs_scope="D:/test", intervention="Stop and do X instead")
        assert prompt.startswith("# ⚠️ PRIORITY MANAGER INTERVENTION (MANDATORY OVERRIDE)")
        assert "Stop and do X instead" in prompt


class TestAntigravityCLIClient:
    @pytest.mark.asyncio
    async def test_run_antigravity_cli_missing_binary(self):
        with patch.object(config, "get_agy_binary", return_value=None):
            res = await run_antigravity_cli("test prompt")
            assert res.success is False
            assert "not found" in (res.error or "")

    @pytest.mark.asyncio
    async def test_run_antigravity_cli_success(self):
        mock_result = (0, [{"type": "text", "content": "done"}], "agy execution complete", "")
        with patch.object(config, "get_agy_binary", return_value="agy.exe"), \
             patch("app.workers.antigravity_worker.agent.cli_client._run_subprocess_sync", return_value=mock_result):
            res = await run_antigravity_cli("test prompt")
            assert res.success is True
            assert "complete" in res.output_text


class TestAntigravityWorkerAgent:
    @pytest.mark.asyncio
    async def test_agent_fails_gracefully_when_binary_missing(self):
        with patch.object(config, "get_agy_binary", return_value=None):
            agent = AntigravityWorkerAgent(objective="Test missing binary")
            step = await agent.decide_next_step()
            assert step["action"] == "fail"
            assert "not found" in step["reason"]

    @pytest.mark.asyncio
    async def test_agent_decide_next_step_runs_milestones_via_cli(self):
        agent = AntigravityWorkerAgent(
            objective="Create test file",
            fs_scope="D:/test",
            model="gemini-3.8-flash-low",
        )
        agent.available = True
        agent.cli_binary = "agy.exe"

        mock_result = RunResult(
            success=True,
            session_id="agy_ses_123",
            output_text="Created test file successfully via agy.",
        )

        with patch("app.workers.antigravity_worker.agent.worker_agent.run_antigravity_cli", new=AsyncMock(return_value=mock_result)):
            step1 = await agent.decide_next_step()
            assert step1["action"] == "tool"
            assert step1["params"]["phase"] == "step"
            assert step1["params"]["milestone_index"] == 1
            assert step1["params"]["session_id"] == "agy_ses_123"

            step2 = await agent.decide_next_step()
            assert step2["action"] == "tool"
            assert step2["params"]["phase"] == "test"
            assert step2["params"]["milestone_index"] == 2

            step3 = await agent.decide_next_step()
            assert step3["action"] == "done"

    @pytest.mark.asyncio
    async def test_intervention_injection_adds_remediation(self):
        agent = AntigravityWorkerAgent(
            objective="Create test file",
            fs_scope="D:/test",
        )
        agent.available = True
        agent.cli_binary = "agy.exe"

        mock_result = RunResult(success=True, output_text="Ok", session_id="agy_ses_456")

        with patch("app.workers.antigravity_worker.agent.worker_agent.run_antigravity_cli", new=AsyncMock(return_value=mock_result)):
            # Advance past step 1
            await agent.decide_next_step()
            # Inject intervention at final test step
            agent.inject_intervention("Change content to 'Updated Text'")
            step_interv = await agent.decide_next_step()
            assert step_interv["params"]["phase"] == "intervention"
            assert "Intervention" in step_interv["params"]["milestone"]


class TestAntigravityEngineIntegration:
    @pytest.mark.asyncio
    async def test_engine_executes_antigravity_loop(self, tmp_path: Path):
        contract = TaskContract(
            objective="Create a simple file in D:/",
            fs_scope=str(tmp_path),
            allowed_tools=[],
            model="gemini-3.8-flash-low",
        )

        def factory(c: TaskContract):
            ag = AntigravityWorkerAgent(
                objective=c.objective,
                fs_scope=c.fs_scope,
                model=c.model,
            )
            ag.available = True
            ag.cli_binary = "agy.exe"
            return ag

        mock_run = AsyncMock(return_value=RunResult(success=True, output_text="Done!", session_id="ses_1"))
        with patch("app.workers.antigravity_worker.agent.worker_agent.run_antigravity_cli", new=mock_run):
            eng = WorkerEngine(registry, agent_factory=factory)
            res = await eng.run(contract)
            assert res["status"] in ("completed", "running")

            if eng._loop_task:
                await eng._loop_task

            state = eng.get_state()
            assert state["status"] == "completed"
            assert len(state["completed"]) >= 2
