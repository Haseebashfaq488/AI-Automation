"""Antigravity Worker Agent implementation.

Drives direct autonomous execution via the Antigravity CLI (`agy run`)
with full session continuity, Master Task Specification prompts,
standard engineering testing protocols, and real-time manager intervention injection.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app.workers.antigravity_worker.agent import config
from app.workers.antigravity_worker.agent.cli_client import RunResult, run_antigravity_cli
from app.workers.antigravity_worker.agent.milestones import (
    build_execution_prompt,
    build_master_task_prompt,
    build_planning_prompt,
    build_testing_prompt,
)
from app.workers.base import bus as bus_mod

logger = logging.getLogger("jarvis.worker.antigravity.agent")


class AntigravityWorkerAgent:
    """Autonomous agent driver powered by Antigravity CLI (`agy`) with 3-Job Lifecycle:
    1. Job 1: Implementation Planning & Blueprint
    2. Job 2: Approved Plan Execution
    3. Job 3: Automated Self-Testing, Verification & Self-Correction
    """

    def __init__(
        self,
        objective: str,
        allowed_tools: List[str] | None = None,
        fs_scope: str = ".",
        requirements: List[str] | None = None,
        constraints: List[str] | None = None,
        success_criteria: List[str] | None = None,
        model: Optional[str] = None,
        master_prompt: Optional[str] = None,
        worker_session_id: Optional[str] = None,
        requires_plan_approval: bool = True,
    ):
        self.objective = objective
        self.fs_scope = fs_scope
        self.requirements = requirements or []
        self.constraints = constraints or []
        self.success_criteria = success_criteria or []
        self.model = model
        self.master_prompt = master_prompt
        self.worker_session_id = worker_session_id
        self.requires_plan_approval = requires_plan_approval

        # Check binary availability for CLI
        self.cli_binary = config.get_agy_binary()
        self.available = self.cli_binary is not None

        # Antigravity session ID for CLI continuity
        self._session_id: Optional[str] = None

        # 3-Job Lifecycle State: planning -> awaiting_approval -> execution -> testing -> done
        self._phase: str = "planning" if not master_prompt else "master_direct"
        self.implementation_plan: Optional[str] = None
        self.test_results: Dict[str, Any] = {}

        # Step results and pending parent interventions
        self._step_results: List[Dict[str, Any]] = []
        self._pending_intervention: Optional[str] = None
        self._execution_summary: Optional[str] = None
        self._step_count: int = 0

    def set_approved_plan(self, plan: str) -> None:
        """Set or update the approved implementation plan and advance to execution."""
        self.implementation_plan = plan
        self._phase = "execution"

    def _make_on_event(self) -> Optional[Callable[[Dict[str, Any]], None]]:
        """Create a real-time event forwarder for SSE consumers."""
        target_ids = []
        if self.worker_session_id:
            target_ids.append(self.worker_session_id)
        if self._session_id and self._session_id not in target_ids:
            target_ids.append(self._session_id)

        def _on_event(ev: Dict[str, Any]) -> None:
            # Also capture agy session id if it appears in stream
            agy_sid = ev.get("conversation_id") or ev.get("conversationId")
            for tid in target_ids:
                bus_mod.emit_to_queues(tid, ev)
            if agy_sid and agy_sid not in target_ids:
                target_ids.append(agy_sid)
                bus_mod.emit_to_queues(agy_sid, ev)

        return _on_event

    def record_step(
        self, tool: str, success: bool, output: Any = None, error: Any = None
    ) -> None:
        """Record step result into agent history."""
        entry: Dict[str, Any] = {"tool": tool, "success": success}
        if error:
            entry["error"] = str(error)[:500]
        if output:
            entry["output"] = str(output)[:500]
        self._step_results.append(entry)

    def inject_intervention(self, message: str) -> None:
        """Queue parent/manager guidance for the next turn."""
        self._pending_intervention = message

    async def decide_next_step(self) -> Dict[str, Any]:
        """Execute autonomous task steps via Antigravity CLI (`agy run`)."""
        current_binary = config.get_agy_binary()
        if not current_binary:
            self.available = False
        if not self.available:
            return {
                "action": "fail",
                "reason": (
                    "Antigravity CLI binary ('agy' or 'antigravity') not found on system PATH. "
                    "Please ensure agy CLI is installed or configure ANTIGRAVITY_BIN in backend/.env"
                ),
            }

        # Handle queued priority intervention
        intervention = self._pending_intervention
        if intervention:
            self._pending_intervention = None
            self._step_count += 1
            if "Plan revision" in intervention or "reject" in intervention.lower():
                self._phase = "planning"
            prompt = (
                f"# ⚠️ PRIORITY MANAGER INTERVENTION DIRECTIVE\n"
                f"{intervention}\n\n"
                f"## Overall Task Context\n{self.objective}\n\n"
                f"Apply the manager's intervention directive immediately and verify results."
            )

            logger.info("Executing Manager Intervention in Antigravity Worker")
            res: RunResult = await run_antigravity_cli(
                prompt,
                session_id=self._session_id,
                work_dir=self.fs_scope,
                model=self.model,
                on_event=self._make_on_event(),
            )
            if res.session_id:
                self._session_id = res.session_id

            if res.success:
                self._execution_summary = res.output_text
                return {
                    "action": "tool",
                    "tool": "apply_intervention",
                    "params": {
                        "step": "Apply Manager Intervention",
                        "message": intervention,
                        "session_id": self._session_id,
                        "output_preview": (res.output_text or "")[:500],
                        "model": self.model or config.get_antigravity_model(),
                    },
                }
            else:
                error_msg = res.error or "Intervention execution error"
                return {
                    "action": "tool",
                    "tool": "apply_intervention",
                    "params": {
                        "step": "Apply Manager Intervention (Failed)",
                        "error": error_msg[:500],
                        "session_id": self._session_id,
                    },
                }

        # Direct override master prompt
        if self._phase == "master_direct":
            self._phase = "done"
            self._step_count += 1
            prompt = self.master_prompt or build_master_task_prompt(
                objective=self.objective,
                fs_scope=self.fs_scope,
                requirements=self.requirements,
                constraints=self.constraints,
                success_criteria=self.success_criteria,
            )
            logger.info("Antigravity Worker executing master task: %s", self.objective[:80])
            res = await run_antigravity_cli(
                prompt,
                session_id=self._session_id,
                work_dir=self.fs_scope,
                model=self.model,
                on_event=self._make_on_event(),
            )
            if res.session_id:
                self._session_id = res.session_id
            if res.success:
                self._execution_summary = res.output_text
                return {
                    "action": "tool",
                    "tool": "task_execution",
                    "params": {
                        "step": "Execute & Verify Task",
                        "objective": self.objective,
                        "session_id": self._session_id,
                        "output_preview": (res.output_text or "")[:500],
                    },
                }
            else:
                return {
                    "action": "tool",
                    "tool": "task_execution",
                    "params": {
                        "step": "Execute Task (Failed)",
                        "error": (res.error or "Execution error")[:500],
                        "session_id": self._session_id,
                    },
                }

        # ── JOB 1: Implementation Planning & Blueprint ───────────────────────
        if self._phase == "planning":
            self._step_count += 1
            prompt = build_planning_prompt(
                objective=self.objective,
                fs_scope=self.fs_scope,
                requirements=self.requirements,
                constraints=self.constraints,
                success_criteria=self.success_criteria,
            )
            logger.info("Antigravity Worker Job 1: Planning for '%s'", self.objective[:80])
            res = await run_antigravity_cli(
                prompt,
                session_id=self._session_id,
                work_dir=self.fs_scope,
                model=self.model,
                on_event=self._make_on_event(),
            )
            if res.session_id:
                self._session_id = res.session_id

            plan_text = res.output_text or ""
            # Check if file was written to disk in fs_scope
            plan_file = Path(self.fs_scope) / "implementation_plan.md"
            if plan_file.is_file():
                try:
                    plan_text = plan_file.read_text(encoding="utf-8")
                except Exception:
                    pass

            self.implementation_plan = plan_text
            self._phase = "awaiting_approval" if self.requires_plan_approval else "execution"

            return {
                "action": "plan_ready",
                "plan": plan_text,
                "params": {
                    "step": "Job 1: Author Implementation Plan",
                    "plan_preview": plan_text[:500],
                    "session_id": self._session_id,
                },
            }

        # If decide_next_step is invoked while phase is awaiting_approval (plan was approved), advance to execution
        if self._phase == "awaiting_approval":
            self._phase = "execution"

        # ── JOB 2: Plan Execution ───────────────────────────────────────────
        if self._phase == "execution":
            self._step_count += 1
            plan_to_run = self.implementation_plan or "Execute the requested objective."
            prompt = build_execution_prompt(
                objective=self.objective,
                fs_scope=self.fs_scope,
                approved_plan=plan_to_run,
                requirements=self.requirements,
                constraints=self.constraints,
            )
            logger.info("Antigravity Worker Job 2: Executing Plan for '%s'", self.objective[:80])
            res = await run_antigravity_cli(
                prompt,
                session_id=self._session_id,
                work_dir=self.fs_scope,
                model=self.model,
                on_event=self._make_on_event(),
            )
            if res.session_id:
                self._session_id = res.session_id

            self._phase = "testing"
            if res.success:
                return {
                    "action": "tool",
                    "tool": "task_execution",
                    "params": {
                        "step": "Job 2: Execute Implementation Plan",
                        "output_preview": (res.output_text or "")[:500],
                        "session_id": self._session_id,
                    },
                }
            else:
                return {
                    "action": "tool",
                    "tool": "task_execution",
                    "params": {
                        "step": "Job 2: Execute Implementation Plan (Failed)",
                        "error": (res.error or "Execution error")[:500],
                        "session_id": self._session_id,
                    },
                }

        # ── JOB 3: Self-Testing, Verification & Self-Correction ─────────────
        if self._phase == "testing":
            self._step_count += 1
            prompt = build_testing_prompt(
                objective=self.objective,
                fs_scope=self.fs_scope,
                success_criteria=self.success_criteria,
            )
            logger.info("Antigravity Worker Job 3: Self-Testing for '%s'", self.objective[:80])
            res = await run_antigravity_cli(
                prompt,
                session_id=self._session_id,
                work_dir=self.fs_scope,
                model=self.model,
                on_event=self._make_on_event(),
            )
            if res.session_id:
                self._session_id = res.session_id

            # Parse test results from disk or output
            test_results: Dict[str, Any] = {"status": "PASSED" if res.success else "FAILED"}
            results_file = Path(self.fs_scope) / "test_results.json"
            if results_file.is_file():
                try:
                    test_results = json.loads(results_file.read_text(encoding="utf-8"))
                except Exception:
                    pass
            self.test_results = test_results
            self._execution_summary = res.output_text or f"Task '{self.objective}' successfully completed."
            self._phase = "done"

            return {
                "action": "tool",
                "tool": "self_testing",
                "params": {
                    "step": "Job 3: Self-Testing & Verification",
                    "test_results": test_results,
                    "output_preview": (res.output_text or "")[:500],
                    "session_id": self._session_id,
                },
            }

        # All 3 jobs complete
        return {
            "action": "done",
            "summary": self._execution_summary or f"Task '{self.objective}' successfully planned, executed, and verified.",
        }

