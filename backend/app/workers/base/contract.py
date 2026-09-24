from pathlib import Path
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator


class TaskContract(BaseModel):
    """The task contract defines what a worker is expected to do, with strict
    validation of objectives, requirements, constraints, and success criteria.

    This is the single source of truth exchanged between the parent and the
    worker during delegation (see OpenCodeAdapter._KNOWN_TOOLS entry
    ``delegate_to_worker``).
    """

    objective: str = Field(
        description="A concise, human-readable description of the overall goal."
    )
    requirements: List[str] = Field(
        default_factory=list,
        description="Explicit requirements the worker must satisfy.",
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Things the worker MUST NOT do.",
    )
    success_criteria: List[str] = Field(
        default_factory=list,
        description="Measurable conditions that signal completion.",
    )
    fs_scope: str = Field(
        description="Base directory the worker is allowed to read/write (absolute path).",
    )
    allowed_tools: List[str] = Field(
        default_factory=list,
        description="Tool names from the global registry that the worker may call.",
    )
    max_steps: int = Field(
        default=20,
        description="Maximum number of execution steps before forced stop.",
    )
    timeout_seconds: Optional[int] = Field(
        default=None,
        description="Hard timeout after which the worker is interrupted.",
    )
    model: Optional[str] = Field(
        default=None,
        description="Optional LLM model override (e.g. gemini-2.5-flash, openai/gpt-oss-120b).",
    )
    task_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the task instance.",
    )
    master_prompt: Optional[str] = Field(
        default=None,
        description="Full synthesized task specification prompt for autonomous execution.",
    )
    testing_spec: Dict[str, Any] = Field(
        default_factory=dict,
        description="Explicit testing guidelines (unit, dataflow, verification criteria).",
    )
    supervisor_enabled: bool = Field(
        default=True,
        description="Whether active stream guardian supervision is enabled for this worker.",
    )
    requires_plan_approval: bool = Field(
        default=True,
        description="Whether the worker requires implementation plan review and approval before execution.",
    )
    plan_status: str = Field(
        default="pending",
        description="Current status of the implementation plan: pending, awaiting_approval, approved, rejected.",
    )
    implementation_plan: Optional[str] = Field(
        default=None,
        description="The detailed implementation plan authored by the worker.",
    )
    test_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured verification and test results recorded by the worker.",
    )
    prior_handover: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Compact session handover brief from prior worker run in this workspace.",
    )
    is_refinement: bool = Field(
        default=False,
        description="Whether this task is an iterative refinement of an existing codebase.",
    )
    folder_manifests: List[str] = Field(
        default_factory=list,
        description="Paths of discovered folder-level README.md living documentation files.",
    )
    has_graphify: bool = Field(
        default=False,
        description="Whether an AST knowledge graph is available at graphify-out/.",
    )

    @field_validator("fs_scope")
    @classmethod
    def fs_scope_must_be_absolute(cls, v: str) -> str:
        import os
        if not v:
            raise ValueError("fs_scope must not be empty")
        # Normalize '/' or '\' root shortcuts to the current drive root
        if v in ("/", "\\"):
            return os.path.abspath(os.sep)
        p = Path(v)
        if not p.is_absolute() and not os.path.isabs(v):
            raise ValueError("fs_scope must be an absolute path")
        return str(p)

    def model_post_init(self, __context) -> None:
        """Ensure default allowed_tools is never None."""
        if self.allowed_tools is None:
            self.allowed_tools = []

    def model_dump_json(self, *args, **kwargs) -> str:
        """Serialize to JSON for transport (parent ↔ worker session init)."""
        return super().model_dump_json(*args, **kwargs)

    @classmethod
    def model_validate_json(cls, s: str) -> "TaskContract":
        """Deserialize from JSON received from the parent."""
        return super().model_validate_json(s)