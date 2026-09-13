from typing import Dict, Any
from pathlib import Path
import shutil
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_exists, validate_path
from app.modules.file_management.helpers.verification import verify_exists


class MoveTool(BaseTool):
    name = "move"
    description = "Move a file or directory to a new location."
    risk = RiskLevel.MEDIUM
    input_schema = {
        "type": "object",
        "properties": {
            "source": {"type": "string"},
            "destination": {"type": "string"},
            "dry_run": {"type": "boolean", "default": False},
        },
        "required": ["source", "destination"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        src = resolve_path(params["source"])
        dst = resolve_path(params["destination"])
        dry = params.get("dry_run", False)
        if dry:
            return {"dry_run": True, "action": f"Would move {src} to {dst}"}
        ensure_exists(src)
        validate_path(src)
        validate_path(dst)
        # Ensure destination parent exists
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return {"moved": True, "source": str(src), "destination": str(dst), **verify_exists(dst)}
