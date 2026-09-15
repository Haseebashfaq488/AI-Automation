"""OpenCode Worker Agent — Jarvis's coding worker brain.

Implements the agent interface required by ``WorkerEngine``:
  - ``available: bool``
  - ``async decide_next_step() -> dict``
  - ``record_step(tool, success, output, error)``
  - ``inject_intervention(message)``

The agent progresses through milestones (Analyze → Implement →
Test/Fix → Verify), sending each as a prompt to OpenCode via the
non-interactive CLI client while maintaining the same OpenCode session
across all milestones.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.workers.opencode_worker.agent.cli_client import run_opencode, RunResult
from app.workers.opencode_worker.agent import config
from app.workers.opencode_worker.agent.milestones import (
    Milestone,
    build_prompt,
    plan_milestones,
)

logger = logging.getLogger("jarvis.worker.opencode.agent")


class OpenCodeWorkerAgent:
    """The OpenCode worker's brain.

    Drives a milestone-based workflow: for each step the engine asks for,
    the agent picks the next uncompleted milestone, builds a prompt, runs
    ``opencode run`` in the same session, and reports back.

    When no ``opencode`` binary is found, ``available`` is ``False`` and
    the engine falls back to its deterministic placeholder loop.
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

        # Check availability
        self.available = config.get_opencode_binary() is not None

        # Plan milestones
        self._milestones = plan_milestones(
            objective,
            requirements=requirements,
            constraints=constraints,
            success_criteria=success_criteria,
        )
        self._current_idx = 0

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

        # Build prompt with optional intervention
        intervention = self._pending_intervention
        self._pending_intervention = None
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
            # OpenCode reported failure — retry once, then signal failure
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
