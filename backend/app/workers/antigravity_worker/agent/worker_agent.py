"""Antigravity Worker Agent implementation.

Drives direct autonomous execution via the Antigravity CLI (`agy run`)
with full session continuity, Master Task Specification prompts,
standard engineering testing protocols, and real-time manager intervention injection.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.workers.antigravity_worker.agent import config
from app.workers.antigravity_worker.agent.cli_client import RunResult, run_antigravity_cli
from app.workers.antigravity_worker.agent.milestones import build_master_task_prompt

logger = logging.getLogger("jarvis.worker.antigravity.agent")


class AntigravityWorkerAgent:
    """Autonomous agent driver powered by Antigravity CLI (`agy`)."""

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
    ):
        self.objective = objective
        self.fs_scope = fs_scope
        self.requirements = requirements or []
        self.constraints = constraints or []
        self.success_criteria = success_criteria or []
        self.model = model
        self.master_prompt = master_prompt

        # Check binary availability for CLI
        self.cli_binary = config.get_agy_binary()
        self.available = self.cli_binary is not None

        # Antigravity session ID for CLI continuity
        self._session_id: Optional[str] = None

        # Step results and pending parent interventions
        self._step_results: List[Dict[str, Any]] = []
        self._pending_intervention: Optional[str] = None
        self._execution_summary: Optional[str] = None
        self._executed_autonomous: bool = False
        self._step_count: int = 0

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

        # Check for queued parent intervention
        intervention = self._pending_intervention
        if intervention:
            self._pending_intervention = None
            self._step_count += 1
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

        # Main Task Execution
        if not self._executed_autonomous:
            self._executed_autonomous = True
            self._step_count += 1

            prompt = self.master_prompt or build_master_task_prompt(
                objective=self.objective,
                fs_scope=self.fs_scope,
                requirements=self.requirements,
                constraints=self.constraints,
                success_criteria=self.success_criteria,
            )

            logger.info("Antigravity Worker executing task: %s", self.objective[:80])
            res: RunResult = await run_antigravity_cli(
                prompt,
                session_id=self._session_id,
                work_dir=self.fs_scope,
                model=self.model,
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
                        "model": self.model or config.get_antigravity_model(),
                    },
                }
            else:
                error_msg = res.error or "CLI execution error"
                logger.warning("Antigravity CLI execution failed: %s", error_msg)
                return {
                    "action": "tool",
                    "tool": "task_execution",
                    "params": {
                        "step": "Execute & Verify Task (Failed)",
                        "error": error_msg[:500],
                        "session_id": self._session_id,
                    },
                }

        # All execution complete
        return {
            "action": "done",
            "summary": self._execution_summary or f"Task '{self.objective}' successfully completed.",
        }
