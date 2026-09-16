"""Unit tests for the OpenCode CLI Worker integration.

Covers:
  - Configuration loading and binary resolution
  - Event parsing and session ID extraction
  - Non-interactive CLI client (mocked subprocess)
  - Dynamic milestone decomposition & prompt building
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
from app.workers.opencode_worker.agent.milestones import (
    Milestone,
    MilestonePhase,
    build_prompt,
    is_simple_task,
    plan_milestones,
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


# ── Dynamic Milestone Decomposition & Prompt Building ───────────────────


class TestMilestones:
    def test_plan_milestones_simple_task_one_step_plus_fixed_test(self):
        """A simple task creates exactly 1 execution step + 1 fixed test step (2 modules)."""
        milestones = plan_milestones("Create a file in local disk D and write the text lorem ipsum into it")
        assert len(milestones) == 2
        assert milestones[0].phase == MilestonePhase.STEP
        assert milestones[1].phase == MilestonePhase.TEST
        assert "Test" in milestones[1].title

    def test_plan_milestones_moderate_task_creates_proportional_steps(self):
        """Moderate task with multiple requirements decomposes into moderate steps + fixed test."""
        milestones = plan_milestones(
            "Refactor auth system and add token refresh endpoint",
            requirements=["Use JWT tokens", "Support refresh"]
        )
        assert len(milestones) == 3
        assert milestones[0].phase == MilestonePhase.STEP
        assert milestones[1].phase == MilestonePhase.STEP
        assert milestones[2].phase == MilestonePhase.TEST

    def test_plan_milestones_always_ends_with_test(self):
        """Every generated plan must end with the fixed TEST milestone."""
        for obj in [
            "Create a file in D",
            "Refactor auth endpoints and run full integration test suite with migration"
        ]:
            ms = plan_milestones(obj)
            assert ms[-1].phase == MilestonePhase.TEST
            assert "Test" in ms[-1].title

    def test_plan_milestones_includes_objective_in_instructions(self):
        milestones = plan_milestones("Add pagination to API")
        for m in milestones:
            assert "Add pagination to API" in m.instructions

    def test_plan_milestones_includes_requirements(self):
        milestones = plan_milestones(
            "Refactor auth system and add token refresh", requirements=["Use JWT tokens", "Support refresh"]
        )
        step = milestones[0]
        assert "Use JWT tokens" in step.instructions
        assert "Support refresh" in step.instructions

    def test_plan_milestones_includes_constraints(self):
        milestones = plan_milestones(
            "Refactor auth system and add token refresh", constraints=["Do not modify user model"]
        )
        step = milestones[0]
        assert "Do not modify user model" in step.instructions

    def test_build_prompt_includes_fs_scope(self):
        m = Milestone(
            phase=MilestonePhase.STEP,
            title="Execute",
            instructions="Look at the project",
        )
        prompt = build_prompt(m, "/home/user/project")
        assert "/home/user/project" in prompt

    def test_build_prompt_places_intervention_at_top_with_override_banner(self):
        m = Milestone(
            phase=MilestonePhase.STEP,
            title="Implement",
            instructions="Write the code",
        )
        prompt = build_prompt(m, "/project", intervention="Change text to I am haseeb")
        # Line 1 MUST be the priority override banner
        assert prompt.startswith("# ⚠️ PRIORITY MANAGER INTERVENTION (MANDATORY OVERRIDE)")
        assert "Change text to I am haseeb" in prompt
        assert "CRITICAL DIRECTIVE" in prompt


# ── Argument Builder & Output Parsing ───────────────────────────────────


class TestCliClientHelpers:
    def test_build_args_basic(self, monkeypatch):
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: "/usr/bin/opencode",
        )
        args = _build_args("do something", work_dir="/project")
        assert args[0] == "/usr/bin/opencode"
        assert args[1] == "run"
        assert args[2] == "do something"
        assert "--dir" in args
        assert args[args.index("--dir") + 1] == "/project"
        assert "--format" in args
        assert args[args.index("--format") + 1] == "json"
        assert "--auto" in args

    def test_build_args_includes_session_when_provided(self, monkeypatch):
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: "/usr/bin/opencode",
        )
        args = _build_args("step 2", session_id="ses_abc123")
        assert "--session" in args
        assert args[args.index("--session") + 1] == "ses_abc123"

    def test_build_args_raises_when_no_binary(self, monkeypatch):
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: None,
        )
        with pytest.raises(FileNotFoundError):
            _build_args("prompt")

    def test_extract_session_id_from_event(self):
        events = [{"type": "step_start", "sessionID": "ses_456"}]
        assert _extract_session_id(events, "") == "ses_456"

    def test_extract_session_id_from_raw_text(self):
        events = [{"type": "text", "content": "hello"}]
        raw = "Session ses_abc123def started"
        assert _extract_session_id(events, raw) == "ses_abc123def"

    def test_extract_session_id_none_when_missing(self):
        events = [{"type": "text", "content": "nothing here"}]
        assert _extract_session_id(events, "no session") is None


# ── Worker Agent & Parent Intervention ──────────────────────────────────


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
            objective="Create a file in local disk D and write lorem ipsum into it",
            allowed_tools=[],
            fs_scope="/project",
        )
        # Simple task -> 2 milestones (1 step + 1 fixed test)
        assert len(agent._milestones) == 2
        assert agent._milestones[0].phase == MilestonePhase.STEP
        assert agent._milestones[1].phase == MilestonePhase.TEST

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
        assert result["params"]["milestone_index"] == 1
        assert agent._opencode_session_id == "ses_test123"

    @pytest.mark.asyncio
    async def test_session_continuity_across_milestones(self, monkeypatch):
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

        # Milestone 1
        r1 = await agent.decide_next_step()
        assert r1["action"] == "tool"
        agent.record_step("opencode_milestone", True)

        # Milestone 2 — should reuse session
        r2 = await agent.decide_next_step()
        assert r2["action"] == "tool"
        agent.record_step("opencode_milestone", True)

        assert call_log[0] is None
        assert call_log[1] == "ses_persistent"

    @pytest.mark.asyncio
    async def test_all_milestones_complete_signals_done(self, monkeypatch):
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
            objective="Create file D:/test.txt", allowed_tools=[], fs_scope="/project"
        )

        # Run through all milestones
        total = len(agent._milestones)
        for _ in range(total):
            r = await agent.decide_next_step()
            assert r["action"] == "tool"
            agent.record_step("opencode_milestone", True)

        # Now should be done
        final = await agent.decide_next_step()
        assert final["action"] == "done"
        assert "All milestones completed" in final["summary"]

    @pytest.mark.asyncio
    async def test_intervention_included_in_prompt_at_line_one(self, monkeypatch):
        """Verify that inject_intervention text appears prominently at the top of the prompt."""
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
            objective="Create file D:/haseeb.txt", allowed_tools=[], fs_scope="/project"
        )
        agent.inject_intervention("Please prioritize the auth module")

        await agent.decide_next_step()
        assert len(captured_prompts) == 1
        assert captured_prompts[0].startswith("# ⚠️ PRIORITY MANAGER INTERVENTION (MANDATORY OVERRIDE)")
        assert "Please prioritize the auth module" in captured_prompts[0]

    @pytest.mark.asyncio
    async def test_late_intervention_inserts_remediation_milestone(self, monkeypatch):
        """When an intervention arrives on the final test step, an intervention remediation
        milestone is dynamically inserted before testing so the worker doesn't finish without it."""
        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.config.get_opencode_binary",
            lambda: "opencode",
        )

        captured = []

        async def fake_run(prompt, **kw):
            captured.append(prompt)
            return RunResult(success=True, session_id="ses_late", output_text="OK", events=[])

        monkeypatch.setattr(
            "app.workers.opencode_worker.agent.worker_agent.run_opencode",
            fake_run,
        )

        agent = OpenCodeWorkerAgent(
            objective="Create file D:/test.txt", allowed_tools=[], fs_scope="/project"
        )
        # Run step 0
        r0 = await agent.decide_next_step()
        assert r0["action"] == "tool"
        agent.record_step("opencode_milestone", True)

        # We are now at step 1 (final test step). Inject late intervention!
        agent.inject_intervention("Change content to I am haseeb")

        # decide_next_step should execute the dynamic INTERVENTION milestone
        r_interv = await agent.decide_next_step()
        assert r_interv["action"] == "tool"
        assert r_interv["params"]["phase"] == MilestonePhase.INTERVENTION.value
        agent.record_step("opencode_milestone", True)

        # Next is the TEST milestone
        r_test = await agent.decide_next_step()
        assert r_test["action"] == "tool"
        assert r_test["params"]["phase"] == MilestonePhase.TEST.value
        agent.record_step("opencode_milestone", True)

        # Done
        final = await agent.decide_next_step()
        assert final["action"] == "done"

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

        assert engine._loop_task is not None
        final_state = await engine._loop_task
        assert final_state["success"] is True
        assert final_state["completed_steps"] >= 2
        assert "milestone_test" in final_state["tools_used"]
