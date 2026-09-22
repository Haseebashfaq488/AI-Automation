"""Worker Agent — drives the OpenCode CLI loop.

Directly executes autonomous tasks via OpenCode CLI (`opencode run`),
preserves session continuity, injects parent interventions,
and reports real-time execution progress back to Jarvis.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.workers.opencode_worker.agent import config
from app.workers.opencode_worker.agent.cli_client import RunResult, run_opencode

logger = logging.getLogger("jarvis.worker.opencode.agent")


class OpenCodeWorkerAgent:
    """Autonomous agent driving OpenCode CLI execution for a background worker."""

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

        # OpenCode session ID (set after the first run, reused for continuity)
        self._opencode_session_id: Optional[str] = None

        # Step history (compact, used for logging)
        self._step_results: List[Dict[str, Any]] = []

        # Parent interventions queued for the next turn
        self._pending_intervention: Optional[str] = None
        self._executed: bool = False
        self._execution_summary: Optional[str] = None

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
        """Queue guidance from the parent (user / Jarvis) for the next turn."""
        self._pending_intervention = message

    async def decide_next_step(self) -> Dict[str, Any]:
        """Return the next action for the engine loop."""
        if not self.available:
            return {
                "action": "fail",
                "reason": (
                    "OpenCode binary not found. Set OPENCODE_BIN in .env "
                    "or ensure `opencode` is on PATH."
                ),
            }

        # Check for queued parent intervention
        intervention = self._pending_intervention
        if intervention:
            self._pending_intervention = None
            prompt = (
                f"# PRIORITY PARENT AGENT DIRECTIVE\n"
                f"{intervention}\n\n"
                f"Task Context: {self.objective}\n"
                f"Apply the parent directive immediately and verify the changes."
            )

            logger.info("Executing parent intervention in OpenCode worker")
            res: RunResult = await run_opencode(
                prompt=prompt,
                cwd=self.fs_scope,
                session_id=self._opencode_session_id,
            )
            if res.session_id:
                self._opencode_session_id = res.session_id

            if res.success:
                self._execution_summary = res.output_text
                return {
                    "action": "tool",
                    "tool": "apply_intervention",
                    "params": {
                        "step": "Apply Manager Intervention",
                        "message": intervention,
                        "session_id": self._opencode_session_id,
                        "output_preview": (res.output_text or "")[:500],
                    },
                }
            else:
                return {
                    "action": "tool",
                    "tool": "apply_intervention",
                    "params": {
                        "step": "Apply Manager Intervention (Failed)",
                        "error": res.error or "Intervention execution error",
                        "session_id": self._opencode_session_id,
                    },
                }

        # Execute main task
        if not self._executed:
            self._executed = True
            reqs = "\n".join(f"- {r}" for r in self.requirements) if self.requirements else "- None specified"
            consts = "\n".join(f"- {c}" for c in self.constraints) if self.constraints else "- Stay in fs_scope"
            crit = "\n".join(f"- {s}" for s in self.success_criteria) if self.success_criteria else "- Verify all files are created and tests pass"

            prompt = (
                f"# Master Task Specification\n\n"
                f"## Objective\n{self.objective}\n\n"
                f"## Working Directory\n{self.fs_scope}\n\n"
                f"## Requirements\n{reqs}\n\n"
                f"## Constraints\n{consts}\n\n"
                f"## Success Criteria\n{crit}\n\n"
                f"Execute the task fully, write all files, and verify test passes."
            )

            logger.info("OpenCode Worker executing task: %s", self.objective[:80])
            res: RunResult = await run_opencode(
                prompt=prompt,
                work_dir=self.fs_scope,
                session_id=self._opencode_session_id,
            )

            if res.session_id:
                self._opencode_session_id = res.session_id

            if res.success:
                self._execution_summary = res.output_text
                return {
                    "action": "tool",
                    "tool": "task_execution",
                    "params": {
                        "step": "Execute & Verify Task",
                        "objective": self.objective,
                        "session_id": self._opencode_session_id,
                        "output_preview": (res.output_text or "")[:500],
                    },
                }
            else:
                error_msg = res.error or "Execution failed"
                return {
                    "action": "tool",
                    "tool": "task_execution",
                    "params": {
                        "step": "Execute & Verify Task (Failed)",
                        "error": error_msg[:500],
                        "session_id": self._opencode_session_id,
                    },
                }

        return {
            "action": "done",
            "summary": self._execution_summary or f"Task '{self.objective}' completed.",
        }
