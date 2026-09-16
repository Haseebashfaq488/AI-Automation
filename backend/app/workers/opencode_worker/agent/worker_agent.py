"""Worker Agent — drives the OpenCode CLI loop.

Replaces the placeholder loop with a real LLM-backed agent that delegates
milestones to OpenCode via ``opencode run``, preserves session continuity,
injects parent interventions, and reports progress back to Jarvis.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.workers.opencode_worker.agent import config
from app.workers.opencode_worker.agent.cli_client import RunResult, run_opencode
from app.workers.opencode_worker.agent.milestones import (
    Milestone,
    MilestonePhase,
    build_prompt,
    plan_milestones,
    plan_milestones_llm_async,
)

logger = logging.getLogger("jarvis.worker.opencode.agent")


class OpenCodeWorkerAgent:
    """Autonomous agent driving OpenCode CLI execution for a background worker.

    Follows a dynamic milestone-based workflow:
      1. Simple tasks (create file, write text) run in 1 step + 1 fixed test step.
      2. Moderate tasks run in 2-3 steps + 1 fixed test step.
      3. Parent interventions are injected at line 1 with mandatory override priority.
    """

    def __init__(
        self,
        objective: str,
        allowed_tools: List[str],
        fs_scope: str,
        requirements: List[str] | None = None,
        constraints: List[str] | None = None,
        success_criteria: List[str] | None = None,
    ):
        self.objective = objective
        self.allowed_tools = list(allowed_tools)
        self.fs_scope = fs_scope
        self.requirements = requirements or []
        self.constraints = constraints or []
        self.success_criteria = success_criteria or []

        # Check availability
        self.available = config.get_opencode_binary() is not None

        # Plan milestones (heuristic baseline initially, refined via LLM on step 1)
        self._milestones = plan_milestones(
            objective,
            requirements=self.requirements,
            constraints=self.constraints,
            success_criteria=self.success_criteria,
        )
        self._current_idx = 0
        self._llm_planned = False

        # OpenCode session ID (set after the first run, reused for continuity)
        self._opencode_session_id: Optional[str] = None

        # Step history (compact, used for logging)
        self._step_results: List[Dict[str, Any]] = []

        # Parent interventions queued for the next milestone
        self._pending_intervention: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API used by the engine loop
    # ------------------------------------------------------------------

    def record_step(
        self, tool: str, success: bool, output: Any = None, error: Any = None
    ) -> None:
        """Append a compact result the next decision will see."""
        entry: Dict[str, Any] = {"tool": tool, "success": success}
        if error:
            entry["error"] = str(error)[:500]
        if output:
            entry["output"] = str(output)[:500]
        self._step_results.append(entry)

    def inject_intervention(self, message: str) -> None:
        """Queue guidance from the parent (user / Jarvis) for the next milestone."""
        self._pending_intervention = message

    async def decide_next_step(self) -> Dict[str, Any]:
        """Return the next action for the engine loop.

        Returns one of:
          - ``{"action": "tool", "tool": "opencode_milestone", "params": {...}}``
          - ``{"action": "done", "summary": "..."}``
          - ``{"action": "fail", "reason": "..."}``
        """
        if not self.available:
            return {
                "action": "fail",
                "reason": "opencode CLI binary not found on PATH",
            }

        # Step 0: attempt LLM dynamic decomposition if not already run
        if not self._llm_planned and self._current_idx == 0:
            self._llm_planned = True
            try:
                llm_milestones = await plan_milestones_llm_async(
                    self.objective,
                    requirements=self.requirements,
                    constraints=self.constraints,
                    success_criteria=self.success_criteria,
                )
                if llm_milestones:
                    self._milestones = llm_milestones
            except Exception as exc:
                logger.debug("LLM dynamic milestone decomposition skipped: %s", exc)

        # Handle queued parent intervention
        intervention = self._pending_intervention
        if intervention:
            self._pending_intervention = None

            # If already on or past the final test milestone, insert an intervention remediation milestone
            # so the worker executes the user's guidance before concluding!
            if self._current_idx >= len(self._milestones) - 1:
                interv_m = Milestone(
                    phase=MilestonePhase.INTERVENTION,
                    title="Apply Manager Intervention",
                    instructions=(
                        f"## Priority Intervention Directive\n{intervention}\n\n"
                        f"## Overall Task Context\n{self.objective}\n\n"
                        f"## Action Required\nApply the user's intervention instructions immediately before final verification."
                    ),
                    verification_criteria=["Intervention instructions applied"],
                )
                if self._current_idx < len(self._milestones):
                    self._milestones.insert(self._current_idx, interv_m)
                else:
                    self._milestones.append(interv_m)
                    self._milestones.append(
                        Milestone(
                            phase=MilestonePhase.TEST,
                            title="Test & Verify After Intervention",
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

        # Build prompt with optional intervention at Line 1
        prompt = build_prompt(milestone, self.fs_scope, intervention=intervention)

        logger.info(
            "Milestone %d/%d [%s]: %s",
            self._current_idx + 1,
            len(self._milestones),
            milestone.phase.value,
            milestone.title,
        )

        # Run OpenCode
        result: RunResult = await run_opencode(
            prompt,
            session_id=self._opencode_session_id,
            work_dir=self.fs_scope,
        )

        # Capture session ID for continuity
        if result.session_id:
            self._opencode_session_id = result.session_id

        # Evaluate result
        if result.success:
            milestone.completed = True
            milestone.result_summary = (
                result.output_text[:1000] if result.output_text else "completed"
            )
            self._current_idx += 1

            return {
                "action": "tool",
                "tool": "opencode_milestone",
                "params": {
                    "milestone": milestone.title,
                    "phase": milestone.phase.value,
                    "milestone_index": self._current_idx,  # already incremented
                    "total_milestones": len(self._milestones),
                    "opencode_session": self._opencode_session_id,
                    "output_preview": (result.output_text or "")[:500],
                },
            }
        else:
            # OpenCode reported failure
            error_msg = result.error or "unknown error"
            logger.warning(
                "Milestone %d failed: %s", self._current_idx + 1, error_msg
            )
            return {
                "action": "tool",
                "tool": "opencode_milestone",
                "params": {
                    "milestone": milestone.title,
                    "phase": milestone.phase.value,
                    "milestone_index": self._current_idx + 1,
                    "total_milestones": len(self._milestones),
                    "opencode_session": self._opencode_session_id,
                    "error": error_msg[:500],
                },
            }
