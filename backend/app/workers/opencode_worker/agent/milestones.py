"""Milestone Planner & Prompt Builder for Jarvis → OpenCode orchestration.

Jarvis breaks each coding task into a sequence of logical milestones.
This module models those milestones and generates the structured prompts
that OpenCode receives for each one.

The milestones are *not* arbitrary chunks of text — they map to the
actual stages of software work: analyse → implement → test/fix → verify.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class MilestonePhase(str, Enum):
    """High-level phases a coding task progresses through."""
    ANALYZE = "analyze"
    IMPLEMENT = "implement"
    TEST_FIX = "test_fix"
    VERIFY = "verify"


@dataclass
class Milestone:
    """A single milestone in a task's lifecycle."""
    phase: MilestonePhase
    title: str
    instructions: str
    verification_criteria: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    completed: bool = False
    result_summary: Optional[str] = None


def plan_milestones(
    objective: str,
    requirements: List[str] | None = None,
    constraints: List[str] | None = None,
    success_criteria: List[str] | None = None,
) -> List[Milestone]:
    """Generate a default sequence of milestones for a coding task.

    This is the *deterministic* planner — it always produces the same
    four-phase pipeline. A future LLM-driven planner can override this
    when more sophisticated milestone decomposition is needed.
    """
    reqs = requirements or []
    cons = constraints or []
    crit = success_criteria or []

    reqs_text = "\n".join(f"  - {r}" for r in reqs) if reqs else "  (none specified)"
    cons_text = "\n".join(f"  - {c}" for c in cons) if cons else "  (none specified)"
    crit_text = "\n".join(f"  - {c}" for c in crit) if crit else "  (none specified)"

    return [
        Milestone(
            phase=MilestonePhase.ANALYZE,
            title="Analyze Project & Plan Implementation",
            instructions=(
                f"## Overall Task\n{objective}\n\n"
                f"## Current Milestone: Analyze\n"
                f"Inspect the project to understand the existing codebase. Identify:\n"
                f"  - Relevant source files and their structure\n"
                f"  - Existing patterns, conventions, and dependencies\n"
                f"  - What needs to change or be created\n"
                f"  - Potential risks or conflicts\n\n"
                f"## Requirements\n{reqs_text}\n\n"
                f"## Constraints\n{cons_text}\n\n"
                f"## What to report\n"
                f"Summarize your findings: which files are relevant, what approach you recommend, "
                f"and any blockers you foresee. Do NOT start implementation yet."
            ),
            verification_criteria=["Analysis report with identified files and approach"],
        ),
        Milestone(
            phase=MilestonePhase.IMPLEMENT,
            title="Implement Changes",
            instructions=(
                f"## Overall Task\n{objective}\n\n"
                f"## Current Milestone: Implement\n"
                f"Based on the analysis from the previous milestone, implement the required changes.\n"
                f"  - Create or modify the necessary files\n"
                f"  - Follow existing project conventions\n"
                f"  - Write clean, well-documented code\n\n"
                f"## Requirements\n{reqs_text}\n\n"
                f"## Constraints\n{cons_text}\n\n"
                f"## What to report\n"
                f"List every file you created or modified and briefly describe each change."
            ),
            verification_criteria=["Implementation complete", "Files listed"],
            constraints=constraints or [],
        ),
        Milestone(
            phase=MilestonePhase.TEST_FIX,
            title="Run Tests & Fix Failures",
            instructions=(
                f"## Overall Task\n{objective}\n\n"
                f"## Current Milestone: Test & Fix\n"
                f"Run the project's test suite (e.g. pytest, npm test) and check for failures.\n"
                f"  - If tests fail, inspect the failures and fix the code\n"
                f"  - Re-run the tests until they pass\n"
                f"  - If new tests are needed, write them\n\n"
                f"## Success Criteria\n{crit_text}\n\n"
                f"## What to report\n"
                f"Final test output: how many passed, how many failed. If anything still fails, "
                f"explain what went wrong and what you tried."
            ),
            verification_criteria=["Tests executed", "Pass/fail report provided"],
        ),
        Milestone(
            phase=MilestonePhase.VERIFY,
            title="Final Verification & Summary",
            instructions=(
                f"## Overall Task\n{objective}\n\n"
                f"## Current Milestone: Final Verification\n"
                f"Review all changes made during this task:\n"
                f"  - Verify the implementation meets the requirements\n"
                f"  - Check for any regressions or unintended side effects\n"
                f"  - Produce a final summary of what was accomplished\n\n"
                f"## Success Criteria\n{crit_text}\n\n"
                f"## What to report\n"
                f"A concise final summary: what was done, what was tested, "
                f"what succeeded, what failed (if anything), and what remains (if anything)."
            ),
            verification_criteria=["Final summary provided"],
        ),
    ]


def build_prompt(milestone: Milestone, fs_scope: str, intervention: str | None = None) -> str:
    """Build the full prompt string sent to ``opencode run``.

    Parameters
    ----------
    milestone:
        The current milestone to execute.
    fs_scope:
        The project directory the worker operates in.
    intervention:
        Optional parent/user guidance injected mid-task.
    """
    parts = [milestone.instructions]

    parts.append(f"\n## Project Directory\n{fs_scope}")

    if intervention:
        parts.append(
            f"\n## Manager Guidance (Important — Read Carefully)\n{intervention}"
        )

    parts.append(
        "\n## Output Format\n"
        "When you finish this milestone, end your response with a clear "
        "summary of what you accomplished and whether you consider the "
        "milestone successful or if something is still unresolved."
    )

    return "\n".join(parts)
