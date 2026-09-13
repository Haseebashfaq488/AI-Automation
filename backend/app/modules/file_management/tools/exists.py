from typing import Dict, Any
from pathlib import Path
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path


class ExistsTool(BaseTool):
    name = "exists"
    description = "Check whether a given path exists (file or directory)."
    risk = RiskLevel.LOW
    input_schema = {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        raw_path = params["path"]
        path = resolve_path(raw_path)
        # No validation needed beyond existence check
        return {"path": str(path), "exists": path.exists()}
