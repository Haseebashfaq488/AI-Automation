"""Unit tests for the OpenCode CLI Worker integration.

Covers:
  - Configuration loading and binary resolution
  - Event parsing and session ID extraction
  - Non-interactive CLI client (mocked subprocess)
  - Direct task execution & Master Task Specification prompt building
  - OpenCodeWorkerAgent decision loop, session continuity, and parent intervention
"""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.workers.opencode_worker.agent.cli_client import (
    RunResult,
    _build_args,
    _extract_session_id,
    run_opencode,
)
from app.workers.opencode_worker.agent.config import (
    get_auto_approve,
    get_milestone_timeout,
    get_opencode_binary,
    get_opencode_model,
)
from app.workers.opencode_worker.agent.worker_agent import OpenCodeWorkerAgent


# ── Configuration & Binary Resolution ───────────────────────────────────


class TestConfig:
    def test_get_opencode_binary_env_override(self, monkeypatch, tmp_path):
        fake_bin = tmp_path / "opencode.exe"
        fake_bin.touch()
        monkeypatch.setenv("OPENCODE_BIN", str(fake_bin))
        assert get_opencode_binary() == str(fake_bin)

    def test_get_opencode_binary_none_when_missing(self, monkeypatch):
        monkeypatch.delenv("OPENCODE_BIN", raising=False)
        monkeypatch.setattr("shutil.which", lambda _: None)
        monkeypatch.setattr("os.path.isfile", lambda _: False)
        assert get_opencode_binary() is None

    def test_get_opencode_model_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENCODE_MODEL", "groq/llama-3.3-70b-versatile")
        assert get_opencode_model() == "groq/llama-3.3-70b-versatile"

    def test_get_opencode_model_none_by_default(self, monkeypatch):
        monkeypatch.delenv("OPENCODE_MODEL", raising=False)
        assert get_opencode_model() is None

    def test_get_auto_approve_defaults_true(self, monkeypatch):
        monkeypatch.delenv("OPENCODE_AUTO", raising=False)
        assert get_auto_approve() is True

    def test_get_auto_approve_can_be_disabled(self, monkeypatch):
        monkeypatch.setenv("OPENCODE_AUTO", "0")
        assert get_auto_approve() is False

    def test_get_milestone_timeout_defaults_to_300(self, monkeypatch):
        monkeypatch.delenv("OPENCODE_MILESTONE_TIMEOUT", raising=False)
        assert get_milestone_timeout() == 300


# ── Direct Task Execution & Decision Loop ────────────────────────────────


class TestOpenCodeWorkerAgent:
    @pytest.mark.asyncio
    async def test_agent_fails_gracefully_when_binary_missing(self, monkeypatch):
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: None,
        )
        agent = OpenCodeWorkerAgent(
            objective="Do task", allowed_tools=[], fs_scope="/project"
        )
        result = await agent.decide_next_step()
        assert result["action"] == "fail"
        assert "not found" in result["reason"]

    @pytest.mark.asyncio
    async def test_decide_next_step_runs_task(self, monkeypatch):
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: "opencode",
        )

        async def fake_run(prompt, *, session_id=None, work_dir=None, **kw):
            return RunResult(
                success=True,
                session_id="ses_test123",
                output_text="Task output",
                events=[],
            )

        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.worker_agent.run_opencode",
            fake_run,
        )

        agent = OpenCodeWorkerAgent(
            objective="Create file D:/haseeb.txt", allowed_tools=[], fs_scope="/project"
        )

        result = await agent.decide_next_step()
        assert result["action"] == "tool"
        assert result["tool"] == "task_execution"
        assert result["params"]["step"] == "Execute & Verify Task"
        assert agent._opencode_session_id == "ses_test123"

        final = await agent.decide_next_step()
        assert final["action"] == "done"
        assert final["summary"] == "Task output"

    @pytest.mark.asyncio
    async def test_session_continuity_with_intervention(self, monkeypatch):
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: "opencode",
        )

        call_log = []

        async def fake_run(prompt, *, session_id=None, work_dir=None, **kw):
            call_log.append(session_id)
            return RunResult(
                success=True,
                session_id="ses_persistent",
                output_text="Done",
                events=[],
            )

        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.worker_agent.run_opencode",
            fake_run,
        )

        agent = OpenCodeWorkerAgent(
            objective="Create file D:/haseeb.txt", allowed_tools=[], fs_scope="/project"
        )

        # Step 1: Main task
        r1 = await agent.decide_next_step()
        assert r1["action"] == "tool"
        agent.record_step("task_execution", True)

        # Inject parent intervention
        agent.inject_intervention("Prioritize database tests")
        r2 = await agent.decide_next_step()
        assert r2["action"] == "tool"
        assert r2["tool"] == "apply_intervention"
        agent.record_step("apply_intervention", True)

        assert call_log[0] is None
        assert call_log[1] == "ses_persistent"

    @pytest.mark.asyncio
    async def test_engine_runs_opencode_agent_loop(self, tmp_path, monkeypatch):
        """Verify WorkerEngine._agent_loop runs task execution steps and completes."""
        from app.workers.base.contract import TaskContract
        from app.workers.base.engine import WorkerEngine
        from app.workers.base.session import WorkerSession
        from app.registry import registry

        monkeypatch.setattr(WorkerSession, "SESSIONS_ROOT", tmp_path / "sessions")
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: "opencode",
        )

        async def fake_run(prompt, **kw):
            return RunResult(
                success=True,
                session_id="ses_engine_test",
                output_text="Task execution succeeded",
                events=[],
            )

        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.worker_agent.run_opencode",
            fake_run,
        )

        contract = TaskContract(
            objective="Engine integration test",
            fs_scope=str(tmp_path),
            allowed_tools=["list_directory"],
            max_steps=10,
        )

        engine = WorkerEngine(
            registry,
            agent_factory=lambda c: OpenCodeWorkerAgent(
                c.objective, c.allowed_tools, c.fs_scope
            ),
        )

        result = await engine.run(contract)
        assert result["status"] in ("running", "completed")

        assert engine._loop_task is not None
        final_state = await engine._loop_task
        assert final_state["success"] is True
        assert final_state["completed_steps"] >= 1
