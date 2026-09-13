from typing import Dict, Any
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_exists, ensure_is_file, validate_path
from app.modules.file_management.helpers.trash import move_to_trash


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Delete a file. By default it is moved to the Jarvis trash (recoverable); pass permanent=true to delete forever."
    risk = RiskLevel.HIGH

    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "permanent": {"type": "boolean", "default": False},
            "dry_run": {"type": "boolean", "default": False},
        },
        "required": ["path"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_path(params["path"])
        permanent = params.get("permanent", False)
        dry = params.get("dry_run", False)
        ensure_exists(path)
        ensure_is_file(path)
        validate_path(path)
        if dry:
            return {"dry_run": True, "action": f"Would {'permanently delete' if permanent else 'trash'} file {path}"}
        if permanent:
            path.unlink()
            return {"deleted": True, "permanent": True, "path": str(path)}
        trash_path = move_to_trash(path)
        return {"deleted": True, "permanent": False, "path": str(path), "trash_path": str(trash_path)}
