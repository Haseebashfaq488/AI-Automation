"""Tests for the OpenCode CLI Worker Agent.

Covers milestone generation, prompt building, CLI argument construction,
session continuity, and the agent's decide_next_step loop with a mocked
CLI client.
"""
import asyncio
import json

import pytest

from app.workers.opencode_worker.agent.config import (
    get_opencode_binary,
    get_opencode_model,
    get_auto_approve,
    get_milestone_timeout,
)
from app.workers.opencode_worker.agent.milestones import (
    Milestone,
    MilestonePhase,
    build_prompt,
    plan_milestones,
)
from app.workers.opencode_worker.agent.cli_client import (
    RunResult,
    _build_args,
    _extract_session_id,
)
from app.workers.opencode_worker.agent.worker_agent import OpenCodeWorkerAgent


# ── Config ──────────────────────────────────────────────────────────────


class TestConfig:
    def test_get_opencode_model_default(self, monkeypatch):
        monkeypatch.delenv("OPENCODE_MODEL", raising=False)
        assert get_opencode_model() is None




    def test_get_opencode_model_override(self, monkeypatch):
        monkeypatch.setenv("OPENCODE_MODEL", "opencode/gpt-5")
        assert get_opencode_model() == "opencode/gpt-5"

    def test_auto_approve_default(self, monkeypatch):
        monkeypatch.delenv("OPENCODE_AUTO", raising=False)
        assert get_auto_approve() is True

    def test_auto_approve_disabled(self, monkeypatch):
        monkeypatch.setenv("OPENCODE_AUTO", "0")
        assert get_auto_approve() is False

    def test_milestone_timeout_default(self, monkeypatch):
        monkeypatch.delenv("OPENCODE_MILESTONE_TIMEOUT", raising=False)
        assert get_milestone_timeout() == 300

    def test_milestone_timeout_override(self, monkeypatch):
        monkeypatch.setenv("OPENCODE_MILESTONE_TIMEOUT", "60")
        assert get_milestone_timeout() == 60


# ── Milestones ──────────────────────────────────────────────────────────


class TestMilestones:
    def test_plan_milestones_generates_four_phases(self):
        milestones = plan_milestones("Build auth system")
        assert len(milestones) == 4
        phases = [m.phase for m in milestones]
        assert phases == [
            MilestonePhase.ANALYZE,
            MilestonePhase.IMPLEMENT,
            MilestonePhase.TEST_FIX,
            MilestonePhase.VERIFY,
        ]

    def test_plan_milestones_includes_objective_in_instructions(self):
        milestones = plan_milestones("Add pagination to API")
        for m in milestones:
            assert "Add pagination to API" in m.instructions

    def test_plan_milestones_includes_requirements(self):
        milestones = plan_milestones(
            "Refactor auth", requirements=["Use JWT tokens", "Support refresh"]
        )
        analyze = milestones[0]
        assert "Use JWT tokens" in analyze.instructions
        assert "Support refresh" in analyze.instructions

    def test_plan_milestones_includes_constraints(self):
        milestones = plan_milestones(
            "Refactor auth", constraints=["Do not modify user model"]
        )
        implement = milestones[1]
        assert "Do not modify user model" in implement.instructions

    def test_build_prompt_includes_fs_scope(self):
        m = Milestone(
            phase=MilestonePhase.ANALYZE,
            title="Analyze",
            instructions="Look at the project",
        )
        prompt = build_prompt(m, "/home/user/project")
        assert "/home/user/project" in prompt

    def test_build_prompt_includes_intervention(self):
        m = Milestone(
            phase=MilestonePhase.IMPLEMENT,
            title="Implement",
            instructions="Write the code",
        )
        prompt = build_prompt(m, "/project", intervention="Focus on the API routes")
        assert "Focus on the API routes" in prompt
        assert "Manager Guidance" in prompt

    def test_build_prompt_without_intervention(self):
        m = Milestone(
            phase=MilestonePhase.VERIFY,
            title="Verify",
            instructions="Check everything",
        )
        prompt = build_prompt(m, "/project")
        assert "Manager Guidance" not in prompt


# ── CLI Client ──────────────────────────────────────────────────────────


class TestCLIClient:
    def test_build_args_basic(self, monkeypatch):
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: "/usr/bin/opencode",
        )
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_model",
            lambda: "opencode/test-model",
        )
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_auto_approve",
            lambda: True,
        )
        args = _build_args("hello world")
        assert args[0] == "/usr/bin/opencode"
        assert args[1] == "run"
        assert "hello world" in args
        assert "--model" in args
        assert "opencode/test-model" in args
        assert "--format" in args
        assert "json" in args
        assert "--auto" in args

    def test_build_args_with_session(self, monkeypatch):
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: "opencode",
        )
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_model",
            lambda: "m",
        )
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_auto_approve",
            lambda: False,
        )
        args = _build_args("do stuff", session_id="ses_abc123", work_dir="/proj")
        assert "--session" in args
        idx = args.index("--session")
        assert args[idx + 1] == "ses_abc123"
        assert "--dir" in args
        idx = args.index("--dir")
        assert args[idx + 1] == "/proj"
        assert "--auto" not in args

    def test_build_args_raises_without_binary(self, monkeypatch):
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: None,
        )
        with pytest.raises(FileNotFoundError):
            _build_args("test")

    def test_extract_session_id_from_events(self):
        events = [{"type": "init", "sessionID": "ses_xyz789"}]
        assert _extract_session_id(events, "") == "ses_xyz789"

    def test_extract_session_id_from_raw_text(self):
        events = [{"type": "text", "content": "hello"}]
        raw = "Session ses_abc123def started"
        assert _extract_session_id(events, raw) == "ses_abc123def"

    def test_extract_session_id_none_when_missing(self):
        events = [{"type": "text", "content": "nothing here"}]
        assert _extract_session_id(events, "no session") is None


# ── Worker Agent ────────────────────────────────────────────────────────


class TestOpenCodeWorkerAgent:
    def test_agent_unavailable_when_no_binary(self, monkeypatch):
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: None,
        )
        agent = OpenCodeWorkerAgent(
            objective="test", allowed_tools=[], fs_scope="/tmp"
        )
        assert agent.available is False

    def test_agent_available_when_binary_exists(self, monkeypatch):
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: "/usr/bin/opencode",
        )
        agent = OpenCodeWorkerAgent(
            objective="test", allowed_tools=[], fs_scope="/tmp"
        )
        assert agent.available is True

    @pytest.mark.asyncio
    async def test_decide_next_step_fails_when_unavailable(self, monkeypatch):
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: None,
        )
        agent = OpenCodeWorkerAgent(
            objective="test", allowed_tools=[], fs_scope="/tmp"
        )
        result = await agent.decide_next_step()
        assert result["action"] == "fail"
        assert "not found" in result["reason"]

    def test_milestones_planned_on_init(self, monkeypatch):
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: "opencode",
        )
        agent = OpenCodeWorkerAgent(
            objective="Build feature X",
            allowed_tools=[],
            fs_scope="/project",
            requirements=["Must be fast"],
        )
        assert len(agent._milestones) == 4
        assert agent._milestones[0].phase == MilestonePhase.ANALYZE

    def test_record_step(self, monkeypatch):
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: "opencode",
        )
        agent = OpenCodeWorkerAgent(
            objective="test", allowed_tools=[], fs_scope="/tmp"
        )
        agent.record_step("opencode_milestone", True, output="done")
        assert len(agent._step_results) == 1
        assert agent._step_results[0]["success"] is True

    def test_inject_intervention(self, monkeypatch):
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: "opencode",
        )
        agent = OpenCodeWorkerAgent(
            objective="test", allowed_tools=[], fs_scope="/tmp"
        )
        agent.inject_intervention("Focus on the API module")
        assert agent._pending_intervention == "Focus on the API module"

    @pytest.mark.asyncio
    async def test_decide_next_step_runs_milestone(self, monkeypatch):
        """Mock run_opencode to simulate a successful milestone and verify
        the agent progresses to the next milestone."""
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: "opencode",
        )

        async def fake_run(prompt, *, session_id=None, work_dir=None, **kw):
            return RunResult(
                success=True,
                session_id="ses_test123",
                output_text="Analysis complete. Found 5 relevant files.",
                events=[],
            )

        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.worker_agent.run_opencode",
            fake_run,
        )

        agent = OpenCodeWorkerAgent(
            objective="Add logging", allowed_tools=[], fs_scope="/project"
        )
        result = await agent.decide_next_step()
        assert result["action"] == "tool"
        assert result["tool"] == "opencode_milestone"
        assert result["params"]["phase"] == "analyze"
        assert result["params"]["milestone_index"] == 1
        assert agent._opencode_session_id == "ses_test123"

    @pytest.mark.asyncio
    async def test_session_continuity_across_milestones(self, monkeypatch):
        """Verify the same session ID is passed to subsequent milestones."""
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
            objective="Test continuity", allowed_tools=[], fs_scope="/project"
        )

        # Milestone 1 (analyze)
        r1 = await agent.decide_next_step()
        assert r1["action"] == "tool"
        agent.record_step("opencode_milestone", True)

        # Milestone 2 (implement) — should reuse session
        r2 = await agent.decide_next_step()
        assert r2["action"] == "tool"
        agent.record_step("opencode_milestone", True)

        # First call had no session, second should have the persistent one
        assert call_log[0] is None
        assert call_log[1] == "ses_persistent"

    @pytest.mark.asyncio
    async def test_all_milestones_complete_signals_done(self, monkeypatch):
        """After all 4 milestones complete, decide_next_step returns done."""
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: "opencode",
        )

        async def fake_run(prompt, **kw):
            return RunResult(success=True, session_id="ses_x", output_text="OK", events=[])

        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.worker_agent.run_opencode",
            fake_run,
        )

        agent = OpenCodeWorkerAgent(
            objective="Complete task", allowed_tools=[], fs_scope="/project"
        )

        # Run through all 4 milestones
        for _ in range(4):
            r = await agent.decide_next_step()
            assert r["action"] == "tool"
            agent.record_step("opencode_milestone", True)

        # Now should be done
        final = await agent.decide_next_step()
        assert final["action"] == "done"
        assert "All milestones completed" in final["summary"]

    @pytest.mark.asyncio
    async def test_intervention_included_in_prompt(self, monkeypatch):
        """Verify that inject_intervention text appears in the milestone prompt."""
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: "opencode",
        )

        captured_prompts = []

        async def fake_run(prompt, *, session_id=None, work_dir=None, **kw):
            captured_prompts.append(prompt)
            return RunResult(success=True, session_id="ses_i", output_text="OK", events=[])

        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.worker_agent.run_opencode",
            fake_run,
        )

        agent = OpenCodeWorkerAgent(
            objective="Fix bugs", allowed_tools=[], fs_scope="/project"
        )
        agent.inject_intervention("Please prioritize the auth module")

        await agent.decide_next_step()
        assert len(captured_prompts) == 1
        assert "Please prioritize the auth module" in captured_prompts[0]

    @pytest.mark.asyncio
    async def test_engine_runs_opencode_agent_loop(self, tmp_path, monkeypatch):
        """Verify WorkerEngine._agent_loop runs opencode_milestone steps and completes."""
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
                output_text="Milestone succeeded",
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
        assert result["status"] == "running"

        # Wait for background loop task
        assert engine._loop_task is not None
        final_state = await engine._loop_task
        assert final_state["success"] is True
        assert final_state["completed_steps"] == 4
        assert "milestone_analyze" in final_state["tools_used"]
        assert "milestone_verify" in final_state["tools_used"]

