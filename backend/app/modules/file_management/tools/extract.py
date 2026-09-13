import zipfile
from typing import Dict, Any, List
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_exists, ensure_is_file, validate_path


class ExtractTool(BaseTool):
    name = "extract"
    description = "Extract a .zip archive into a destination folder (safe against zip-slip)."
    risk = RiskLevel.MEDIUM

    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "path of the .zip file"},
            "destination": {"type": "string", "description": "folder to extract into (default: next to the zip)"},
            "dry_run": {"type": "boolean", "default": False},
        },
        "required": ["path"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        src = resolve_path(params["path"])
        ensure_exists(src)
        ensure_is_file(src)
        validate_path(src)
        if params.get("destination"):
            dst = resolve_path(params["destination"])
        else:
            dst = src.parent / src.stem
        validate_path(dst)
        dry = params.get("dry_run", False)
        if dry:
            return {"dry_run": True, "action": f"Would extract {src} into {dst}"}

        dst.mkdir(parents=True, exist_ok=True)
        dest_root = dst.resolve()
        with zipfile.ZipFile(src, "r") as zf:
            members: List[str] = zf.namelist()
            for member in members:
                target = (dst / member).resolve()
                if not str(target).startswith(str(dest_root)):
                    raise ValueError(f"Unsafe path in archive: {member}")
            zf.extractall(dst)
        return {
            "extracted": True,
            "path": str(src),
            "destination": str(dst),
            "file_count": len(members),
            "members": members,
        }
