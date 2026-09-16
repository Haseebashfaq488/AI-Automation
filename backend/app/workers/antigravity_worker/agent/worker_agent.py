"""Antigravity Worker Agent implementation.

Drives autonomous milestone execution via the Antigravity CLI (`agy run`)
with full session continuity across milestones, milestone decomposition,
and manager intervention injection.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.workers.antigravity_worker.agent import config
from app.workers.antigravity_worker.agent.cli_client import RunResult, run_antigravity_cli
from app.workers.antigravity_worker.agent.milestones import (
    Milestone,
    MilestonePhase,
    build_prompt,
    plan_milestones,
)

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
    ):
        self.objective = objective
        self.fs_scope = fs_scope
        self.requirements = requirements or []
        self.constraints = constraints or []
        self.success_criteria = success_criteria or []
        self.model = model

        # Check binary availability for CLI
        self.cli_binary = config.get_agy_binary()
        self.available = self.cli_binary is not None

        # Plan proportional milestones
        self._milestones: List[Milestone] = plan_milestones(
            objective,
            requirements=self.requirements,
            constraints=self.constraints,
            success_criteria=self.success_criteria,
        )
        self._current_idx = 0

        # Antigravity session ID for CLI continuity
        self._session_id: Optional[str] = None

        # Step results and pending parent interventions
        self._step_results: List[Dict[str, Any]] = []
        self._pending_intervention: Optional[str] = None

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
        """Queue parent/manager guidance for the next milestone."""
        self._pending_intervention = message

    async def decide_next_step(self) -> Dict[str, Any]:
        """Execute the next milestone via Antigravity CLI (`agy run`)."""
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

            # Late intervention remediation milestone injection
            if self._current_idx >= len(self._milestones) - 1:
                interv_m = Milestone(
                    phase=MilestonePhase.INTERVENTION,
                    title="Apply Manager Intervention",
                    instructions=(
                        f"## Priority Intervention Directive\n{intervention}\n\n"
                        f"## Overall Task Context\n{self.objective}\n\n"
                        f"## Action Required\nApply the user's intervention directive immediately before concluding."
                    ),
                    verification_criteria=["Intervention applied"],
                )
                if self._current_idx < len(self._milestones):
                    self._milestones.insert(self._current_idx, interv_m)
                else:
                    self._milestones.append(interv_m)
                    self._milestones.append(
                        Milestone(
                            phase=MilestonePhase.TEST,
                            title="Verify After Intervention",
                            instructions=f"Verify all changes including the intervention:\n{intervention}",
                            verification_criteria=["Changes and intervention verified"],
                        )
                    )

        # All milestones done?
        if self._current_idx >= len(self._milestones):
            summaries = [
                f"[{m.phase.value}] {m.title}: {m.result_summary or 'completed'}"
                for m in self._milestones
            ]
            return {
                "action": "done",
                "summary": "All milestones completed.\n" + "\n".join(summaries),
            }

        milestone = self._milestones[self._current_idx]
        prompt = build_prompt(milestone, self.fs_scope, intervention=intervention)

        logger.info(
            "Antigravity Milestone %d/%d [%s]: %s",
            self._current_idx + 1,
            len(self._milestones),
            milestone.phase.value,
            milestone.title,
        )

        phase_val = milestone.phase.value

        # Execute via agy run CLI
        res: RunResult = await run_antigravity_cli(
            prompt,
            session_id=self._session_id,
            work_dir=self.fs_scope,
            model=self.model,
        )

        if res.session_id:
            self._session_id = res.session_id

        if res.success:
            milestone.completed = True
            milestone.result_summary = (res.output_text or "completed")[:1000]
            self._current_idx += 1

            return {
                "action": "tool",
                "tool": "opencode_milestone",
                "params": {
                    "milestone": milestone.title,
                    "phase": phase_val,
                    "milestone_index": self._current_idx,
                    "total_milestones": len(self._milestones),
                    "session_id": self._session_id,
                    "output_preview": (res.output_text or "")[:500],
                    "model": self.model or config.get_antigravity_model(),
                },
            }
        else:
            error_msg = res.error or "Unknown CLI execution error"
            logger.warning("Antigravity CLI milestone %d failed: %s", self._current_idx + 1, error_msg)
            return {
                "action": "tool",
                "tool": "opencode_milestone",
                "params": {
                    "milestone": milestone.title,
                    "phase": phase_val,
                    "milestone_index": self._current_idx + 1,
                    "total_milestones": len(self._milestones),
                    "session_id": self._session_id,
                    "error": error_msg[:500],
                },
            }
