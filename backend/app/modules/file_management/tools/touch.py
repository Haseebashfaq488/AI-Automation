import os
from typing import Dict, Any
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import validate_path


class TouchTool(BaseTool):
    name = "touch"
    description = "Create an empty file if it does not exist, otherwise update its modified timestamp."
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
        created = not path.exists()
        if dry:
            return {"dry_run": True, "action": f"Would {'create' if created else 'touch'} {path}"}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
        if not created:
            os.utime(path, None)  # update timestamps to now
        stat = path.stat()
        return {
            "path": str(path),
            "created": created,
            "modified_at": stat.st_mtime,
            "size": stat.st_size,
        }
