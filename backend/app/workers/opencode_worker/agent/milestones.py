"""Milestone Planner & Prompt Builder for Jarvis → OpenCode orchestration.

Jarvis breaks each coding task into a sequence of moderate, logical milestones.
The milestone decomposition is dynamic:
- Simple tasks (e.g. create a file, write text) go in 1 execution step + 1 fixed test step.
- Moderate tasks go in 2-3 moderate execution steps + 1 fixed test step.
- The final module is ALWAYS fixed: a dedicated Test & Verify milestone.
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("jarvis.worker.milestones")


class MilestonePhase(str, Enum):
    """High-level phases a coding task progresses through."""
    STEP = "step"                    # Dynamic execution module
    TEST = "test"                    # Fixed final testing/verification module
    INTERVENTION = "intervention"    # Dynamically injected on parent intervention

    # Aliases for backward compatibility
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


# ── Complexity Heuristics ────────────────────────────────────────────────

_SIMPLE_PATTERNS = [
    r"^create\s+(?:a\s+)?(?:text\s+)?file",
    r"^write\s+",
    r"^make\s+(?:a\s+)?(?:new\s+)?(?:folder|directory|file)",
    r"^delete\s+",
    r"^remove\s+",
    r"^rename\s+",
    r"^touch\s+",
    r"^inspect\s+",
    r"^check\s+(?:if\s+)?(?:a\s+)?file",
    r"^copy\s+",
    r"^move\s+",
]


def is_simple_task(objective: str, requirements: List[str] | None = None) -> bool:
    """Check if an objective is a simple single-step operation."""
    if requirements and len(requirements) >= 2:
        return False

    cleaned = objective.strip().lower()

    # Moderate/complex indicators
    compound_indicators = [
        "refactor", "system", "pipeline", "architecture", "integrate",
        "full stack", "migration", "database", "authentication"
    ]
    if any(ci in cleaned for ci in compound_indicators):
        return False

    for pat in _SIMPLE_PATTERNS:
        if re.search(pat, cleaned):
            return True

    words = cleaned.split()
    if len(words) <= 10 and not any(c in cleaned for c in [" and ", " then "]):
        return True

    return False


# ── Synchronous Heuristic Planner ───────────────────────────────────────

def plan_milestones(
    objective: str,
    requirements: List[str] | None = None,
    constraints: List[str] | None = None,
    success_criteria: List[str] | None = None,
) -> List[Milestone]:
    """Generate a dynamic sequence of milestones based on task complexity.

    - Simple task: 1 execution step + 1 fixed test step (2 modules total).
    - Moderate task: 2 execution steps + 1 fixed test step (3 modules total).
    - Complex task: 3 execution steps + 1 fixed test step (4 modules total).
    The final module is ALWAYS fixed to test/verification.
    """
    reqs = requirements or []
    cons = constraints or []
    crit = success_criteria or []

    reqs_text = "\n".join(f"  - {r}" for r in reqs) if reqs else "  (none specified)"
    cons_text = "\n".join(f"  - {c}" for c in cons) if cons else "  (none specified)"
    crit_text = "\n".join(f"  - {c}" for c in crit) if crit else "  (verify implementation works as expected)"

    simple = is_simple_task(objective, requirements=reqs)

    if simple:
        # Simple task: 1 execution step + 1 fixed test step
        return [
            Milestone(
                phase=MilestonePhase.STEP,
                title=f"Execute: {objective[:60]}",
                instructions=(
                    f"## Overall Task\n{objective}\n\n"
                    f"## Current Milestone: Implementation\n"
                    f"Perform the requested task directly and accurately:\n"
                    f"  - Create, modify, or inspect the target files as requested.\n"
                    f"  - Ensure file paths, content, and formatting match the instructions exactly.\n\n"
                    f"## Requirements\n{reqs_text}\n\n"
                    f"## Constraints\n{cons_text}\n\n"
                    f"## What to report\n"
                    f"List what actions you performed and what files were created or modified."
                ),
                verification_criteria=["Task executed according to instructions"],
                constraints=cons,
            ),
            Milestone(
                phase=MilestonePhase.TEST,
                title="Test & Verify Implementation",
                instructions=(
                    f"## Overall Task\n{objective}\n\n"
                    f"## Current Milestone: Test & Verification (Final Module)\n"
                    f"Verify that the previous step succeeded and the changes are working correctly:\n"
                    f"  - Verify files exist in their target paths and content is correct.\n"
                    f"  - If applicable, run tests or validation commands.\n\n"
                    f"## Success Criteria\n{crit_text}\n\n"
                    f"## What to report\n"
                    f"State clearly whether the task passed verification and list the confirmed files/results."
                ),
                verification_criteria=["Verification passed", "Final report provided"],
            ),
        ]

    # Moderate or larger task: 2 execution steps + 1 fixed test step
    return [
        Milestone(
            phase=MilestonePhase.STEP,
            title="Analyze & Set Up",
            instructions=(
                f"## Overall Task\n{objective}\n\n"
                f"## Current Milestone: Preparation & Initial Implementation\n"
                f"Inspect the project and prepare the foundational files or structure:\n"
                f"  - Review existing code and directory structure.\n"
                f"  - Set up or modify the core files.\n\n"
                f"## Requirements\n{reqs_text}\n\n"
                f"## Constraints\n{cons_text}\n\n"
                f"## What to report\n"
                f"Summarize the files prepared and initial changes made."
            ),
            verification_criteria=["Preparation and core changes completed"],
            constraints=cons,
        ),
        Milestone(
            phase=MilestonePhase.STEP,
            title="Complete Implementation",
            instructions=(
                f"## Overall Task\n{objective}\n\n"
                f"## Current Milestone: Complete Implementation\n"
                f"Implement the remaining logic, functions, and endpoints needed to satisfy the objective:\n"
                f"  - Finish all file modifications or additions.\n"
                f"  - Ensure clean code following existing conventions.\n\n"
                f"## Requirements\n{reqs_text}\n\n"
                f"## Constraints\n{cons_text}\n\n"
                f"## What to report\n"
                f"List all completed components and modified files."
            ),
            verification_criteria=["Complete implementation achieved"],
            constraints=cons,
        ),
        Milestone(
            phase=MilestonePhase.TEST,
            title="Test & Verify Implementation",
            instructions=(
                f"## Overall Task\n{objective}\n\n"
                f"## Current Milestone: Test & Verification (Final Module)\n"
                f"Run the test suite or verify the implementation:\n"
                f"  - Run tests (e.g. pytest, npm test, or sanity check scripts).\n"
                f"  - Fix any failures if discovered.\n"
                f"  - Verify all success criteria are met.\n\n"
                f"## Success Criteria\n{crit_text}\n\n"
                f"## What to report\n"
                f"Test results: what passed, what failed (if any), and final status summary."
            ),
            verification_criteria=["Tests passed", "Pass/fail verification complete"],
        ),
    ]


# ── Asynchronous LLM-Driven Planner ─────────────────────────────────────

async def plan_milestones_llm_async(
    objective: str,
    requirements: List[str] | None = None,
    constraints: List[str] | None = None,
    success_criteria: List[str] | None = None,
) -> Optional[List[Milestone]]:
    """Use the Groq LLM to decompose the objective into moderate modules with a fixed final test."""
    import httpx
    from app.core.config import settings

    api_key = os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
    if not api_key:
        return None

    model = os.getenv("GROQ_MODEL") or settings.GROQ_MODEL or "openai/gpt-oss-120b"
    base_url = settings.WORKER_LLM_BASE_URL or "https://api.groq.com/openai/v1"

    reqs_str = ", ".join(requirements) if requirements else "None"
    cons_str = ", ".join(constraints) if constraints else "None"
    crit_str = ", ".join(success_criteria) if success_criteria else "Verify functionality"

    system_prompt = (
        "You are Jarvis's Milestone Decomposer. You divide user coding prompts into a sequence of "
        "moderate, practical execution steps for an autonomous worker.\n\n"
        "RULES:\n"
        "1. For simple/easy tasks (e.g. create a file, write text, touch a file, move a file), output EXACTLY 1 execution step.\n"
        "2. For moderate tasks, output 2 execution steps.\n"
        "3. For complex tasks, output 2 or 3 execution steps.\n"
        "4. DO NOT output a test step — a dedicated 'Test & Verify Implementation' milestone is ALWAYS automatically appended at the end.\n"
        "5. Respond with ONLY valid JSON: a JSON array of objects with keys 'title' and 'instructions'.\n"
        "Example output:\n"
        '[{"title": "Create File and Write Content", "instructions": "Create D:/haseeb.txt and write lorem ipsum into it"}]'
    )

    user_prompt = (
        f"Task Objective: {objective}\n"
        f"Requirements: {reqs_str}\n"
        f"Constraints: {cons_str}\n"
        f"Success Criteria: {crit_str}\n\n"
        "Divide this into moderate execution steps (excluding final test)."
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 800,
                },
            )
            if resp.status_code != 200:
                logger.warning("Groq milestone planning HTTP %d: %s", resp.status_code, resp.text[:200])
                return None

            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)

            parsed = json.loads(content)
            if not isinstance(parsed, list) or len(parsed) == 0:
                return None

            milestones: List[Milestone] = []
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                title = item.get("title", "Execute Step").strip()
                instr = item.get("instructions", objective).strip()
                full_instr = (
                    f"## Overall Task\n{objective}\n\n"
                    f"## Current Milestone: {title}\n"
                    f"{instr}\n\n"
                    f"## Requirements\n{reqs_str}\n\n"
                    f"## What to report\n"
                    f"Summarize the specific actions taken and files modified in this step."
                )
                milestones.append(
                    Milestone(
                        phase=MilestonePhase.STEP,
                        title=title,
                        instructions=full_instr,
                        constraints=constraints or [],
                    )
                )

            if not milestones:
                return None

            # Always append the fixed TEST module at the end
            milestones.append(
                Milestone(
                    phase=MilestonePhase.TEST,
                    title="Test & Verify Implementation",
                    instructions=(
                        f"## Overall Task\n{objective}\n\n"
                        f"## Current Milestone: Test & Verification (Final Module)\n"
                        f"Verify the implementation from the previous steps:\n"
                        f"  - Confirm files exist and content is correct.\n"
                        f"  - Run tests or verification commands.\n\n"
                        f"## Success Criteria\n{crit_str}\n\n"
                        f"## What to report\n"
                        f"Report test results and confirm whether the objective has been successfully met."
                    ),
                    verification_criteria=["Tests and verification complete"],
                )
            )
            logger.info("LLM planned %d milestones for objective: %s", len(milestones), objective[:50])
            return milestones

    except Exception as exc:
        logger.warning("Failed to plan milestones with LLM: %s", exc)
        return None


# ── Prompt Builder ───────────────────────────────────────────────────────

def build_prompt(milestone: Milestone, fs_scope: str, intervention: str | None = None) -> str:
    """Build the full prompt string sent to ``opencode run``.

    Places active interventions at the top with mandatory override priority.
    """
    parts: List[str] = []

    # 1. High-priority intervention banner at the very top (Line 1)
    if intervention:
        parts.append(
            "# ⚠️ PRIORITY MANAGER INTERVENTION (MANDATORY OVERRIDE)\n"
            f"The user/manager has intervened with the following priority instruction:\n"
            f"> \"{intervention}\"\n\n"
            "CRITICAL DIRECTIVE: You MUST follow this instruction immediately. "
            "If this guidance contradicts previous plans, earlier steps, or the original task objective, "
            "THIS USER INTERVENTION SUPERSEDES AND OVERRIDES THEM. Adapt your work immediately to satisfy this guidance."
        )

    # 2. Current milestone instructions
    parts.append(milestone.instructions)

    # 3. Project directory context
    parts.append(f"## Project Directory\n{fs_scope}")

    # 4. Secondary reminder of intervention if present
    if intervention:
        parts.append(
            f"## Reminder: Active Intervention Directive\n{intervention}"
        )

    # 5. Tool rules
    parts.append(
        "## Tools & Environment\n"
        "You are an autonomous OpenCode agent equipped with your own native tools for file management, code editing, and terminal execution. "
        "DO NOT attempt to call or use the 'Jarvis' tools. Use ONLY your own built-in capabilities to complete this milestone."
    )

    # 6. Output format instructions
    parts.append(
        "## Output Format\n"
        "When you finish this milestone, end your response with a clear "
        "summary of what you accomplished and whether you consider the "
        "milestone successful or if something is still unresolved."
    )

    return "\n\n".join(parts)
