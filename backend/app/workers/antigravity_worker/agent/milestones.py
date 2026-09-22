"""Milestone planning and prompt generation for the Antigravity Autonomous Worker.

Features:
  1. Instant heuristic decomposition for simple tasks (1 step + 1 fixed test).
  2. Multi-step decomposition for moderate/complex tasks + 1 fixed test.
  3. Priority manager intervention banner at Line 1 with mandatory override directive.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, Dict, List, Optional


class MilestonePhase(str, Enum):
    STEP = "step"
    TEST = "test"
    INTERVENTION = "intervention"


@dataclass
class Milestone:
    """A single discrete unit of work executed by the Antigravity worker."""
    phase: MilestonePhase
    title: str
    instructions: str
    verification_criteria: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    completed: bool = False
    result_summary: Optional[str] = None


def is_simple_task(objective: str) -> bool:
    """Detect if an objective is simple enough to complete in 1 execution step + 1 test."""
    obj = (objective or "").strip().lower()

    if len(obj) < 160:
        simple_verbs = [
            "create a file", "create file", "write a file", "write file",
            "write text", "touch a file", "touch file", "make a file",
            "make file", "create folder", "create directory", "make folder",
            "make directory", "put content", "put text", "append to",
            "delete file", "remove file", "rename file", "move file",
            "copy file", "inspect file", "check file", "list files",
            "list directory", "read file", "show content", "print hello",
            "echo", "hello world", "lorem ipsum",
        ]
        if any(v in obj for v in simple_verbs):
            return True

    words = obj.split()
    if len(words) <= 15 and not any(w in obj for w in ("refactor", "architect", "full stack", "pipeline", "auth")):
        return True

    return False


def plan_milestones(
    objective: str,
    requirements: List[str] | None = None,
    constraints: List[str] | None = None,
    success_criteria: List[str] | None = None,
) -> List[Milestone]:
    """Generate proportional milestone sequence with a fixed final test phase."""
    reqs = list(requirements or [])
    cons = list(constraints or [])
    crit = list(success_criteria or [])

    reqs_text = "\n".join(f"  - {r}" for r in reqs) if reqs else "  - None specified"
    cons_text = "\n".join(f"  - {c}" for c in cons) if cons else "  - Standard repository conventions"
    crit_text = "\n".join(f"  - {s}" for s in crit) if crit else "  - Successful completion of the requested objective"

    # Simple task -> 1 execution step + 1 fixed test step
    if is_simple_task(objective):
        return [
            Milestone(
                phase=MilestonePhase.STEP,
                title="Execute Task",
                instructions=(
                    f"## Overall Task\n{objective}\n\n"
                    f"## Current Milestone: Execution\n"
                    f"Perform all file modifications, code additions, or commands directly:\n"
                    f"  - Complete the core request accurately.\n"
                    f"  - Ensure valid formatting and clean output.\n\n"
                    f"## Requirements\n{reqs_text}\n\n"
                    f"## Constraints\n{cons_text}\n\n"
                    f"## What to report\n"
                    f"Summarize the specific actions taken and files modified."
                ),
                verification_criteria=["Execution complete"],
                constraints=cons,
            ),
            Milestone(
                phase=MilestonePhase.TEST,
                title="Verify Implementation",
                instructions=(
                    f"## Overall Task\n{objective}\n\n"
                    f"## Current Milestone: Test & Verification (Final Module)\n"
                    f"Verify the results from the previous step:\n"
                    f"  - Confirm files exist and content matches requirements.\n"
                    f"  - Run verification checks or commands if applicable.\n\n"
                    f"## Success Criteria\n{crit_text}\n\n"
                    f"## What to report\n"
                    f"Report verification results and confirm whether the objective has been successfully met."
                ),
                verification_criteria=["Verification complete"],
                constraints=cons,
            ),
        ]

    # Moderate/complex task -> 2 execution steps + 1 test step
    return [
        Milestone(
            phase=MilestonePhase.STEP,
            title="Implement Core",
            instructions=(
                f"## Overall Task\n{objective}\n\n"
                f"## Current Milestone: Core Implementation\n"
                f"Implement the requested logic directly in the workspace:\n"
                f"  - Create or update required files directly.\n"
                f"  - Do NOT spend turns scanning or analyzing unrelated directories.\n\n"
                f"## Requirements\n{reqs_text}\n\n"
                f"## Constraints\n{cons_text}\n\n"
                f"## What to report\n"
                f"Summarize core files created/updated."
            ),
            verification_criteria=["Core implementation complete"],
            constraints=cons,
        ),
        Milestone(
            phase=MilestonePhase.STEP,
            title="Finalize Implementation",
            instructions=(
                f"## Overall Task\n{objective}\n\n"
                f"## Current Milestone: Finalize Implementation\n"
                f"Complete all remaining logic, integrations, and components:\n"
                f"  - Finish all modifications.\n"
                f"  - Ensure clean, working code.\n\n"
                f"## Requirements\n{reqs_text}\n\n"
                f"## Constraints\n{cons_text}\n\n"
                f"## What to report\n"
                f"List all completed components."
            ),
            verification_criteria=["Implementation finished"],
            constraints=cons,
        ),
        Milestone(
            phase=MilestonePhase.TEST,
            title="Test & Verify Implementation",
            instructions=(
                f"## Overall Task\n{objective}\n\n"
                f"## Current Milestone: Test & Verification (Final Module)\n"
                f"Run verification checks or test commands:\n"
                f"  - Verify files exist and code runs properly.\n"
                f"  - Fix any issues discovered.\n\n"
                f"## Success Criteria\n{crit_text}\n\n"
                f"## What to report\n"
                f"Test results and confirmation that objective is met."
            ),
            verification_criteria=["Tests passed", "Pass/fail verification complete"],
            constraints=cons,
        ),
    ]


def build_prompt(milestone: Milestone, fs_scope: str, intervention: str | None = None) -> str:
    """Build the prompt for the Antigravity agent milestone."""
    parts: List[str] = []

    # 1. High-priority intervention banner (Line 1)
    if intervention:
        parts.append(
            "# ⚠️ PRIORITY MANAGER INTERVENTION (MANDATORY OVERRIDE)\n"
            f"The user/manager has intervened with the following priority instruction:\n"
            f"> \"{intervention}\"\n\n"
            "CRITICAL DIRECTIVE: You MUST follow this instruction immediately. "
            "If this guidance contradicts previous plans, earlier steps, or the original task objective, "
            "THIS USER INTERVENTION SUPERSEDES AND OVERRIDES THEM. Adapt your work immediately to satisfy this guidance."
        )

    # 2. Milestone instructions
    parts.append(milestone.instructions)

    # 3. Filesystem Scope
    parts.append(f"## Filesystem Scope Boundary\n{fs_scope}")

    # 4. Output format instructions
    parts.append(
        "## Output Format\n"
        "Provide a concise summary of what was accomplished, including files touched and pass/fail status."
    )

    return "\n\n".join(parts)


def build_master_task_prompt(
    objective: str,
    fs_scope: str,
    requirements: List[str] | None = None,
    constraints: List[str] | None = None,
    success_criteria: List[str] | None = None,
    intervention: str | None = None,
) -> str:
    """Build the master task specification prompt for fully autonomous worker execution."""
    reqs = list(requirements or [])
    cons = list(constraints or [])
    crit = list(success_criteria or [])

    reqs_text = "\n".join(f"- {r}" for r in reqs) if reqs else "- Follow standard software engineering best practices"
    cons_text = "\n".join(f"- {c}" for c in cons) if cons else f"- Stay strictly within workspace boundary: {fs_scope}"
    crit_text = "\n".join(f"- [ ] {s}" for s in crit) if crit else "- [ ] Objective fully achieved\n- [ ] Unit tests pass\n- [ ] Dataflow verification complete"

    parts: List[str] = []

    if intervention:
        parts.append(
            "# ⚠️ PRIORITY MANAGER INTERVENTION (MANDATORY OVERRIDE)\n"
            f"The user/manager has intervened with the following priority instruction:\n"
            f"> \"{intervention}\"\n\n"
            "CRITICAL DIRECTIVE: You MUST satisfy this intervention directive before concluding."
        )

    parts.append(
        f"# 🎯 MASTER TASK SPECIFICATION\n\n"
        f"## 1. Primary Objective\n{objective}\n\n"
        f"## 2. Workspace Scope & Boundaries\n"
        f"- Target Root: `{fs_scope}`\n"
        f"- Boundary: All file modifications and created assets must reside strictly inside `{fs_scope}`.\n\n"
        f"## 3. Requirements & Constraints\n"
        f"### Requirements:\n{reqs_text}\n\n"
        f"### Constraints:\n{cons_text}\n\n"
        f"## 4. Mandatory Engineering Execution Protocol\n"
        f"As an autonomous engineer, execute your work in the following structured manner:\n"
        f"1. **Exploration**: Inspect existing code, dependencies, and environment in `{fs_scope}`.\n"
        f"2. **Implementation**: Author clean, resilient, modular code with proper error handling.\n"
        f"3. **Mandatory Testing Protocol**:\n"
        f"   - **Unit Testing**: Create and run test suites covering all isolated functions, classes, and components.\n"
        f"   - **Dataflow & Pipeline Testing**: Verify end-to-end data pipelines, inputs/outputs, and contract boundaries.\n"
        f"   - **Edge Case Validation**: Ensure graceful handling of empty inputs, missing data, and invalid states.\n"
        f"4. **Self-Correction**: Execute the test commands, inspect failures, and resolve any bugs in-place.\n\n"
        f"## 5. Finishing Criteria Checklist\n{crit_text}\n\n"
        f"## 6. Mandatory Final Summary Format\n"
        f"When concluding your execution, emit the following summary block:\n"
        f"```yaml\n"
        f"STATUS: RESOLVED  # [RESOLVED | PARTIALLY_RESOLVED | BLOCKED]\n"
        f"FILES_MODIFIED: []\n"
        f"FILES_CREATED: []\n"
        f"UNIT_TESTS: {{ total: 0, passed: 0, failed: 0 }}\n"
        f"DATAFLOW_TESTS: {{ status: PASSED, details: '...' }}\n"
        f"SUMMARY: 'Detailed explanation of what was achieved and verified.'\n"
        f"```"
    )

    return "\n\n".join(parts)

