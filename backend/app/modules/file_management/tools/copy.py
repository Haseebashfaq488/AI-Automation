from typing import Dict, Any
from pathlib import Path
import shutil
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_exists, validate_path
from app.modules.file_management.helpers.verification import verify_exists


class CopyTool(BaseTool):
    name = "copy"
    description = "Copy a file or directory to a destination path."
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
            return {"dry_run": True, "action": f"Would copy {src} to {dst}"}
        ensure_exists(src)
        validate_path(src)
        validate_path(dst)
        # Ensure destination parent exists
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            shutil.copy2(src, dst)
        elif src.is_dir():
            if dst.exists():
                raise FileExistsError(f"Destination directory already exists: {dst}")
            shutil.copytree(src, dst)
        else:
            raise ValueError(f"Source is neither file nor directory: {src}")
        return {"copied": True, "source": str(src), "destination": str(dst), **verify_exists(dst)}
