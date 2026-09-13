from fastapi import APIRouter, HTTPException
from typing import Any, Dict
from app.core.execution_engine import ExecutionEngine
from app.registry import registry

router = APIRouter(prefix="/tools", tags=["tools"])
engine = ExecutionEngine(registry)

@router.get("/list")
async def list_tools() -> Dict[str, Any]:
    """Return a list of registered tool names and descriptions."""
    tools = []
    for name, tool in registry.list_tools().items():
        tools.append({"name": name, "description": tool.description, "risk": tool.risk.name, "category": getattr(tool, "category", "tool")})
    return {"tools": tools}

@router.post("/run/{tool_name}")
async def run_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool by name with given parameters."""
    try:
        result = await engine.run(tool_name, params)
        return {"success": result.success, "data": result.data, "error": result.error}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
