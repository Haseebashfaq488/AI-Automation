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


def _living_docs_section() -> str:
    return (
        "## 📂 Mandatory Living Documentation Protocol (Tier 1)\n"
        "Whenever you create or modify files inside any subdirectory (e.g. `components/`, `styles/`, `api/`, `utils/`, `tests/`):\n"
        "1. Check if a `README.md` exists in that directory. If so, read it to follow established patterns.\n"
        "2. If `README.md` does not exist, create it with:\n"
        "   - **Purpose**: What this folder/module is for.\n"
        "   - **Key Files & Roles**: 1-line description of each file.\n"
        "   - **Design Patterns & Conventions**: CSS variables, styling patterns, dependencies, or exported symbols.\n"
        "3. Keep every touched folder's `README.md` updated as files are added or modified."
    )


def _testing_safety_guardrails_section() -> str:
    return (
        "## 🛡️ Critical Subprocess & Test Safety Rules (Anti-Hang Invariants)\n"
        "1. **MANDATORY SUBPROCESS TIMEOUTS**:\n"
        "   - Whenever executing commands or child processes (e.g. `subprocess.run`, `subprocess.Popen`, `Popen.communicate`), you MUST specify an explicit timeout (e.g. `timeout=10` or `timeout=15`).\n"
        "   - Unbounded subprocesses without timeouts are strictly prohibited to prevent infinite test hangs.\n"
        "2. **NEVER LAUNCH BLOCKING GUI / INTERACTIVE LOOPS IN TESTS**:\n"
        "   - Never invoke blocking event loops (such as Tkinter `root.mainloop()`, Qt `QApplication.exec()`, or interactive terminal input prompts) inside automated tests or headless verifications.\n"
        "   - For dual GUI/CLI applications, always run CLI tests with the non-interactive/REPL flag (e.g. `--cli`, `--batch`, or piped stdin with exit command).\n"
        "   - For GUI unit tests, instantiate widgets headlessly, call `root.update()` or `root.update_idletasks()`, and immediately tear down with `root.destroy()`."
    )


def _format_handover_section(
    prior_handover: Dict[str, Any] | None = None,
    folder_manifests: List[str] | None = None,
    is_refinement: bool = False,
) -> str:
    if not prior_handover and not is_refinement:
        return ""

    lines = [
        "# 🔄 SESSION CONTINUATION & PRIOR HANDOVER",
        "You are working on an EXISTING project in this workspace.",
    ]
    if prior_handover:
        prev_obj = prior_handover.get("objective")
        if prev_obj:
            lines.append(f"- **Prior Goal**: {prev_obj}")
        decisions = prior_handover.get("architecture_decisions") or []
        if decisions:
            lines.append("- **Established Architecture & Decisions**:")
            for d in decisions[:5]:
                lines.append(f"  • {d}")

    if folder_manifests:
        lines.append(f"- **Discovered Subfolder Docs**: {', '.join(folder_manifests)}")

    has_graphify = prior_handover.get("has_graphify", False) if prior_handover else False
    if has_graphify:
        lines.extend([
            "- **Knowledge Graph (graphify)**: Available at `graphify-out/`",
            "  • Query architecture: `graphify query \"<question>\"`",
            "  • Trace dependencies: `graphify path \"<file_a>\" \"<file_b>\"`",
            "  • Read summary: `graphify-out/GRAPH_REPORT.md`",
        ])

    lines.extend([
        "",
        "### ⚠️ NON-DESTRUCTIVE REFINEMENT RULES:",
        "1. DO NOT wipe, delete, or rewrite the codebase from scratch.",
        "2. Review existing files and subfolder `README.md` docs before editing.",
        "3. If graphify is available, query the knowledge graph to understand architecture in seconds instead of reading all raw files.",
        "4. Make targeted, clean delta edits that preserve the established architecture.",
        "5. Update the relevant subfolder `README.md` docs to document your changes.",
    ])
    return "\n".join(lines)


def build_planning_prompt(
    objective: str,
    fs_scope: str,
    requirements: List[str] | None = None,
    constraints: List[str] | None = None,
    success_criteria: List[str] | None = None,
    intervention: str | None = None,
    prior_handover: Dict[str, Any] | None = None,
    folder_manifests: List[str] | None = None,
    is_refinement: bool = False,
) -> str:
    """Build the prompt for Job 1: Implementation Planning & Architecture Blueprint."""
    reqs = list(requirements or [])
    cons = list(constraints or [])
    crit = list(success_criteria or [])

    reqs_text = "\n".join(f"- {r}" for r in reqs) if reqs else "- Follow standard software engineering best practices"
    cons_text = "\n".join(f"- {c}" for c in cons) if cons else f"- Stay strictly within workspace boundary: {fs_scope}"
    crit_text = "\n".join(f"- [ ] {s}" for s in crit) if crit else "- [ ] Plan accurately reflects all requirements"

    parts: List[str] = []

    handover_banner = _format_handover_section(prior_handover, folder_manifests, is_refinement)
    if handover_banner:
        parts.append(handover_banner)

    if intervention:
        parts.append(
            "# ⚠️ PRIORITY MANAGER INTERVENTION (MANDATORY OVERRIDE)\n"
            f"The user/manager has provided the following guidance/feedback:\n"
            f"> \"{intervention}\"\n\n"
            "CRITICAL DIRECTIVE: Incorporate this guidance into the revised implementation plan."
        )

    parts.append(
        f"# 📋 WORKER JOB 1: IMPLEMENTATION PLANNING & BLUEPRINT\n\n"
        f"## 1. Primary Objective\n{objective}\n\n"
        f"## 2. Workspace Scope & Boundaries\n"
        f"- Target Root: `{fs_scope}`\n\n"
        f"## 3. Requirements & Constraints\n"
        f"### Requirements:\n{reqs_text}\n\n"
        f"### Constraints:\n{cons_text}\n\n"
        f"### Target Success Criteria:\n{crit_text}\n\n"
        f"## 4. Mandatory Instructions for Planning Phase\n"
        f"You are currently in **PLANNING MODE** (Job 1 of 3).\n"
        f"- **DO NOT** write or modify application/production code yet.\n"
        f"- Inspect existing files, read directories, and check existing `README.md` / `SESSION_HANDOVER.md` files to ground your plan.\n"
        f"- Author a comprehensive, step-by-step implementation plan and save it to `{fs_scope}/implementation_plan.md`.\n\n"
        f"{_living_docs_section()}\n\n"
        f"## 5. Required Plan Structure (`implementation_plan.md`)\n"
        f"Your plan must contain the following sections:\n"
        f"1. **Architecture & Design Overview**: Summary of approach, tech stack, and module structure.\n"
        f"2. **Target Files**: List of all files to create, modify, or delete with their exact relative paths.\n"
        f"3. **Living Documentation Plan**: What subfolder `README.md` files will be created/updated.\n"
        f"4. **Step-by-Step Implementation Roadmap**: Ordered list of execution steps (Job 2).\n"
        f"5. **Self-Testing & Verification Plan**: Explicit testing strategy (unit tests, integration checks, test commands) for Job 3 (ensuring subprocess timeouts and non-blocking headless execution).\n"
        f"6. **Edge Cases & Failure Handling**: Identified risks and mitigations.\n\n"
        f"{_testing_safety_guardrails_section()}\n\n"
        f"Write `{fs_scope}/implementation_plan.md` and output the complete markdown plan."
    )

    return "\n\n".join(parts)


def build_execution_prompt(
    objective: str,
    fs_scope: str,
    approved_plan: str,
    requirements: List[str] | None = None,
    constraints: List[str] | None = None,
    intervention: str | None = None,
    prior_handover: Dict[str, Any] | None = None,
    folder_manifests: List[str] | None = None,
    is_refinement: bool = False,
) -> str:
    """Build the prompt for Job 2: Executing the Approved Implementation Plan."""
    reqs = list(requirements or [])
    cons = list(constraints or [])

    reqs_text = "\n".join(f"- {r}" for r in reqs) if reqs else "- Follow standard software engineering best practices"
    cons_text = "\n".join(f"- {c}" for c in cons) if cons else f"- Stay strictly within workspace boundary: {fs_scope}"

    parts: List[str] = []

    handover_banner = _format_handover_section(prior_handover, folder_manifests, is_refinement)
    if handover_banner:
        parts.append(handover_banner)

    if intervention:
        parts.append(
            "# ⚠️ PRIORITY MANAGER INTERVENTION (MANDATORY OVERRIDE)\n"
            f"The user/manager has provided the following instruction:\n"
            f"> \"{intervention}\"\n\n"
            "CRITICAL DIRECTIVE: Adapt execution immediately to satisfy this guidance."
        )

    parts.append(
        f"# ⚡ WORKER JOB 2: PLAN EXECUTION\n\n"
        f"## 1. Primary Objective\n{objective}\n\n"
        f"## 2. Workspace Scope\n`{fs_scope}`\n\n"
        f"## 3. Requirements & Constraints\n"
        f"### Requirements:\n{reqs_text}\n\n"
        f"### Constraints:\n{cons_text}\n\n"
        f"## 4. Approved Implementation Plan\n"
        f"```markdown\n{approved_plan.strip()}\n```\n\n"
        f"{_living_docs_section()}\n\n"
        f"{_testing_safety_guardrails_section()}\n\n"
        f"## 5. Execution Directives\n"
        f"- Execute all steps outlined in the approved implementation plan.\n"
        f"- Author complete, production-ready, modular code.\n"
        f"- Create and update all target files in `{fs_scope}`.\n"
        f"- Keep subfolder `README.md` files updated for each folder touched.\n"
        f"- Conclude with a summary of files created and modified."
    )

    return "\n\n".join(parts)


def build_testing_prompt(
    objective: str,
    fs_scope: str,
    success_criteria: List[str] | None = None,
    testing_spec: Dict[str, Any] | None = None,
    intervention: str | None = None,
) -> str:
    """Build the prompt for Job 3: Automated Self-Testing & Verification."""
    crit = list(success_criteria or [])
    crit_text = "\n".join(f"- [ ] {s}" for s in crit) if crit else "- [ ] Unit tests passing\n- [ ] Dataflow verification successful\n- [ ] Edge cases handled"

    parts: List[str] = []

    if intervention:
        parts.append(
            "# ⚠️ PRIORITY MANAGER INTERVENTION (MANDATORY OVERRIDE)\n"
            f"The user/manager has provided the following instruction:\n"
            f"> \"{intervention}\"\n\n"
            "CRITICAL DIRECTIVE: Verify this guidance during testing."
        )

    parts.append(
        f"# 🧪 WORKER JOB 3: MANDATORY SELF-TESTING & VERIFICATION\n\n"
        f"## 1. Objective Being Verified\n{objective}\n\n"
        f"## 2. Target Workspace\n`{fs_scope}`\n\n"
        f"## 3. Success Criteria Checklist\n{crit_text}\n\n"
        f"{_testing_safety_guardrails_section()}\n\n"
        f"## 4. Mandatory Testing Protocol\n"
        f"As an autonomous engineer, verify your implementation independently:\n"
        f"1. **Create / Run Test Suites**: Write and execute automated test scripts (e.g. `pytest`, unit test scripts, or command assertions) in `{fs_scope}`.\n"
        f"2. **Dataflow & Edge Case Verification**: Verify valid outputs for normal and edge-case inputs.\n"
        f"3. **Self-Correction**: If ANY test or check fails, inspect the error output, modify the code to fix the root cause, and re-run tests until ALL pass.\n"
        f"4. **Output Test Artifact**: Write `{fs_scope}/test_results.json` with the following schema:\n"
        f"```json\n"
        f"{{\n"
        f'  "status": "PASSED",\n'
        f'  "total_tests": 3,\n'
        f'  "passed": 3,\n'
        f'  "failed": 0,\n'
        f'  "verification_summary": "Detailed explanation of tests run and results."\n'
        f"}}\n"
        f"```\n\n"
        f"Conclude with a clear report of test results."
    )

    return "\n\n".join(parts)


def build_master_task_prompt(
    objective: str,
    fs_scope: str,
    requirements: List[str] | None = None,
    constraints: List[str] | None = None,
    success_criteria: List[str] | None = None,
    intervention: str | None = None,
    prior_handover: Dict[str, Any] | None = None,
    folder_manifests: List[str] | None = None,
    is_refinement: bool = False,
) -> str:
    """Build the master task specification prompt for fully autonomous worker execution."""
    reqs = list(requirements or [])
    cons = list(constraints or [])
    crit = list(success_criteria or [])

    reqs_text = "\n".join(f"- {r}" for r in reqs) if reqs else "- Follow standard software engineering best practices"
    cons_text = "\n".join(f"- {c}" for c in cons) if cons else f"- Stay strictly within workspace boundary: {fs_scope}"
    crit_text = "\n".join(f"- [ ] {s}" for s in crit) if crit else "- [ ] Objective fully achieved\n- [ ] Unit tests pass\n- [ ] Dataflow verification complete"

    parts: List[str] = []

    handover_banner = _format_handover_section(prior_handover, folder_manifests, is_refinement)
    if handover_banner:
        parts.append(handover_banner)

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
        f"{_living_docs_section()}\n\n"
        f"{_testing_safety_guardrails_section()}\n\n"
        f"## 4. Mandatory Engineering Execution Protocol\n"
        f"As an autonomous engineer, execute your work in the following structured manner:\n"
        f"1. **Exploration**: Inspect existing code, dependencies, and environment in `{fs_scope}`.\n"
        f"2. **Implementation**: Author clean, resilient, modular code with proper error handling.\n"
        f"3. **Living Documentation**: Ensure every created/modified directory has a concise `README.md`.\n"
        f"4. **Mandatory Testing Protocol**:\n"
        f"   - **Unit Testing**: Create and run test suites covering all isolated functions, classes, and components.\n"
        f"   - **Dataflow & Pipeline Testing**: Verify end-to-end data pipelines, inputs/outputs, and contract boundaries.\n"
        f"   - **Edge Case Validation**: Ensure graceful handling of empty inputs, missing data, and invalid states.\n"
        f"5. **Self-Correction**: Execute the test commands, inspect failures, and resolve any bugs in-place.\n\n"
        f"## 5. Finishing Criteria Checklist\n{crit_text}\n\n"
        f"## 6. Mandatory Final Summary Format\n"
        f"When concluding your execution, emit the following summary block:\n"
        f"```yaml\n"
        f"STATUS: RESOLVED  # [RESOLVED | PARTIALLY_RESOLVED | BLOCKED]\n"
        f"FILES_MODIFIED: []\n"
        f"FILES_CREATED: []\n"
        f"FOLDER_DOCS_UPDATED: []\n"
        f"UNIT_TESTS: {{ total: 0, passed: 0, failed: 0 }}\n"
        f"DATAFLOW_TESTS: {{ status: PASSED, details: '...' }}\n"
        f"SUMMARY: 'Detailed explanation of what was achieved and verified.'\n"
        f"```"
    )

    return "\n\n".join(parts)

