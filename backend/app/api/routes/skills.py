from fastapi import APIRouter, HTTPException
from typing import Any, Dict
from app.core.execution_engine import ExecutionEngine
from app.registry import registry

router = APIRouter(prefix="/skills", tags=["skills"])
engine = ExecutionEngine(registry)

@router.get("/list")
async def list_skills() -> Dict[str, Any]:
    """Return a list of registered skills (category == "skill")."""
    skills = []
    for name, tool in registry.list_tools().items():
        if getattr(tool, "category", "tool") == "skill":
            skills.append({"name": name, "description": tool.description, "risk": tool.risk.name})
    return {"skills": skills}

@router.post("/run/{skill_name}")
async def run_skill(skill_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a skill by name with given parameters."""
    try:
        result = await engine.run(skill_name, params)
        return {"success": result.success, "data": result.data, "error": result.error}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
