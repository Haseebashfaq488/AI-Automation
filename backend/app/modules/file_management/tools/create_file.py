from typing import Dict, Any
from pathlib import Path
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import validate_path
from app.modules.file_management.helpers.verification import verify_exists


class CreateFileTool(BaseTool):
    name = "create_file"
    description = "Create an empty file at the given path."
    risk = RiskLevel.MEDIUM
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "dry_run": {"type": "boolean", "default": False},
        },
        "required": ["path"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_path(params["path"])
        validate_path(path)
        dry = params.get("dry_run", False)
        if dry:
            return {"dry_run": True, "action": f"Would create file {path}"}
        # Ensure parent directory exists
        parent = path.parent
        if not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
        # Create the file if it does not exist
        path.touch(exist_ok=True)
        return {"created": True, "path": str(path), **verify_exists(path)}
