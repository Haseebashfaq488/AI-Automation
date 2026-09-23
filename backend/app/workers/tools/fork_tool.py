"""ForkTool — registered BaseTool for launching autonomous background workers."""
from typing import Any, Dict
from app.core.tool import BaseTool, RiskLevel


class ForkTool(BaseTool):
    name = "fork"
    description = (
        "Fork an autonomous background worker to perform engineering, coding, file creation, "
        "editing, multi-step scripting, and verification tasks in the target workspace."
    )
    risk = RiskLevel.HIGH
    category = "tool"

    input_schema = {
        "type": "object",
        "properties": {
            "objective": {
                "type": "string",
                "description": "Clear and concise description of the task for the worker to execute",
            },
            "fs_scope": {
                "type": "string",
                "description": "Target workspace directory path (defaults to 'D:/workspace')",
                "default": "D:/workspace",
            },
            "worker_type": {
                "type": "string",
                "description": "Engine type to use ('antigravity_worker')",
                "default": "antigravity_worker",
            },
            "requirements": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of explicit technical requirements",
            },
            "constraints": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of boundaries or forbidden modifications",
            },
            "success_criteria": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of measurable pass/fail completion conditions",
            },
            "max_steps": {
                "type": "integer",
                "description": "Maximum steps the worker is allowed to run",
                "default": 20,
            },
            "allowed_tools": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of allowed tool names for the worker",
            },
        },
        "required": ["objective"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a worker fork via the workers router / engine."""
        from app.api.routes.agent import _fork_task
        prompt = params.get("objective", "Forked autonomous worker task")
        res = await _fork_task(params, prompt)
        if not res.get("success"):
            error_info = res.get("error", {})
            err_msg = error_info.get("message", "Failed to fork worker session")
            raise RuntimeError(f"Fork failed: {err_msg}")
        return res.get("data", {})
