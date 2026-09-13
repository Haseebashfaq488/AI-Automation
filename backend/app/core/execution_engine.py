import time
import logging
from typing import Dict, Any
from .tool_result import ToolResult
from .tool import BaseTool
from app.registry.tool_registry import ToolRegistry
from app.core.exceptions import ExecutionError, ValidationError

logger = logging.getLogger("jarvis.execution")


class ExecutionEngine:
    """Core engine that validates input, executes a tool, and returns a ToolResult.

    The engine:
    1. Looks up the tool by name in the provided registry.
    2. Validates the supplied parameters against the tool's ``input_schema`` using
       Pydantic's ``BaseModel`` validation (simple dict check for this example).
    3. Executes the tool's ``execute`` coroutine.
    4. Wraps the raw result in a ``ToolResult`` with success flag, metadata, and
       error information if needed.
    5. Logs execution duration and risk level.
    """

    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.logger = logger

    async def run(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        # 1. Retrieve tool
        try:
            tool: BaseTool = self.registry.get(tool_name)
        except KeyError as exc:
            raise ExecutionError(message=f"Tool '{tool_name}' not found") from exc

        # 2. Simple schema validation – ensure required keys exist
        missing = [k for k in tool.input_schema.get("required", []) if k not in params]
        if missing:
            raise ValidationError(message=f"Missing required parameters: {missing}")

        # 3. Execute tool
        start = time.time()
        try:
            raw_result = await tool.execute(params)
            success = True
            error = None
        except Exception as exc:
            raw_result = None
            success = False
            error = {"code": "EXECUTION_ERROR", "message": str(exc)}
            self.logger.exception("Tool execution failed: %s", tool_name)
        duration_ms = int((time.time() - start) * 1000)

        # 4. Build ToolResult
        result = ToolResult(
            success=success,
            tool=tool_name,
            data=raw_result if success else None,
            error=error,
            metadata={"duration_ms": duration_ms, "risk": tool.risk.value},
        )
        self.logger.info(
            "Executed tool %s (risk=%s) in %d ms", tool_name, tool.risk.value, duration_ms
        )
        return result
