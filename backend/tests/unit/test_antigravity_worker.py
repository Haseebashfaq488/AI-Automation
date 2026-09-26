"""Unit tests for the Antigravity Autonomous Worker (Direct Execution & Streaming Mode)."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.workers.antigravity_worker.agent import config
from app.workers.antigravity_worker.agent.cli_client import RunResult, run_antigravity_cli
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


class TestAntigravityCLIClient:
    @pytest.mark.asyncio
    async def test_run_antigravity_cli_missing_binary(self):
        with patch.object(config, "get_agy_binary", return_value=None):
            res = await run_antigravity_cli("test prompt")
            assert res.success is False
            assert "not found" in (res.error or "")

    @pytest.mark.asyncio
    async def test_run_antigravity_cli_success(self):
        mock_result = (0, [{"type": "text", "content": "done"}], "agy execution complete", "", "agy_ses_123")
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
    async def test_agent_decide_next_step_runs_task_via_cli(self):
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

        with patch.object(config, "get_agy_binary", return_value="agy.exe"), \
             patch("app.workers.antigravity_worker.agent.worker_agent.run_antigravity_cli", new=AsyncMock(return_value=mock_result)):
            # Job 1: Planning
            step1 = await agent.decide_next_step()
            assert step1["action"] == "plan_ready"
            assert step1["params"]["step"] == "Job 1: Author Implementation Plan"
            assert step1["params"]["session_id"] == "agy_ses_123"

            # Approve plan -> advance to Job 2
            agent.set_approved_plan(step1["plan"])

            # Job 2: Execution
            step2 = await agent.decide_next_step()
            assert step2["action"] == "tool"
            assert step2["tool"] == "task_execution"
            assert step2["params"]["step"] == "Job 2: Execute Implementation Plan"

            # Job 3: Self-Testing & Verification
            step3 = await agent.decide_next_step()
            assert step3["action"] == "tool"
            assert step3["tool"] == "self_testing"
            assert step3["params"]["step"] == "Job 3: Self-Testing & Verification"

            # Conclude
            step4 = await agent.decide_next_step()
            assert step4["action"] == "done"
            assert "Created test file" in step4["summary"]

    @pytest.mark.asyncio
    async def test_intervention_injection_executes_intervention(self):
        agent = AntigravityWorkerAgent(
            objective="Create test file",
            fs_scope="D:/test",
        )
        agent.available = True
        agent.cli_binary = "agy.exe"

        mock_result = RunResult(success=True, output_text="Ok", session_id="agy_ses_456")

        with patch.object(config, "get_agy_binary", return_value="agy.exe"), \
             patch("app.workers.antigravity_worker.agent.worker_agent.run_antigravity_cli", new=AsyncMock(return_value=mock_result)):
            # Advance past main task
            await agent.decide_next_step()
            # Inject intervention
            agent.inject_intervention("Change content to 'Updated Text'")
            step_interv = await agent.decide_next_step()
            assert step_interv["action"] == "tool"
            assert step_interv["tool"] == "apply_intervention"
            assert "Apply Manager Intervention" in step_interv["params"]["step"]


class TestAntigravityEngineIntegration:
    @pytest.mark.asyncio
    async def test_engine_executes_antigravity_loop(self, tmp_path: Path):
        contract = TaskContract(
            objective="Create a simple file in D:/",
            fs_scope=str(tmp_path),
            allowed_tools=[],
            model="gemini-3.8-flash-low",
            requires_plan_approval=True,
        )

        def factory(c: TaskContract):
            ag = AntigravityWorkerAgent(
                objective=c.objective,
                fs_scope=c.fs_scope,
                model=c.model,
                requires_plan_approval=c.requires_plan_approval,
            )
            ag.available = True
            ag.cli_binary = "agy.exe"
            return ag

        mock_run = AsyncMock(return_value=RunResult(success=True, output_text="Done!", session_id="ses_1"))
        with patch.object(config, "get_agy_binary", return_value="agy.exe"), \
             patch("app.workers.antigravity_worker.agent.worker_agent.run_antigravity_cli", new=mock_run):
            eng = WorkerEngine(registry, agent_factory=factory)
            res = await eng.run(contract)
            assert res["status"] in ("completed", "running", "awaiting_plan_approval")

            # Let planning complete and wait for approval state
            for _ in range(20):
                if eng.get_state()["status"] == "awaiting_plan_approval":
                    break
                await asyncio.sleep(0.05)

            assert eng.get_state()["status"] == "awaiting_plan_approval"

            # Approve plan to trigger execution and self-testing
            eng.approve_plan("# Approved Plan\n1. Do it.")

            if eng._loop_task:
                await eng._loop_task

            state = eng.get_state()
            assert state["status"] == "completed"
            assert len(state["completed"]) == 3
            assert "Job 1: Author Implementation Plan" in state["completed"]
            assert "Job 2: Execute Implementation Plan" in state["completed"]
            assert "Job 3: Self-Testing & Verification" in state["completed"]
            assert len(state["errors"]) == 0
