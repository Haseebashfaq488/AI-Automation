import zipfile
from typing import Dict, Any, List
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_exists, validate_path


class ArchiveTool(BaseTool):
    name = "archive"
    description = "Create a .zip archive from a file or folder."
    risk = RiskLevel.MEDIUM

    input_schema = {
        "type": "object",
        "properties": {
            "source": {"type": "string"},
            "destination": {"type": "string", "description": "path of the .zip file to create"},
            "dry_run": {"type": "boolean", "default": False},
        },
        "required": ["source", "destination"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        src = resolve_path(params["source"])
        dst = resolve_path(params["destination"])
        dry = params.get("dry_run", False)
        ensure_exists(src)
        validate_path(src)
        validate_path(dst)
        if dst.suffix.lower() != ".zip":
            dst = dst.with_suffix(".zip")
        if dry:
            return {"dry_run": True, "action": f"Would archive {src} into {dst}"}

        dst.parent.mkdir(parents=True, exist_ok=True)
        members: List[str] = []
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zf:
            if src.is_file():
                zf.write(src, arcname=src.name)
                members.append(src.name)
            else:
                for p in sorted(src.rglob("*")):
                    if p.is_file():
                        arcname = str(p.relative_to(src))
                        zf.write(p, arcname=arcname)
                        members.append(arcname)
        return {
            "archived": True,
            "source": str(src),
            "destination": str(dst),
            "file_count": len(members),
            "size_bytes": dst.stat().st_size,
            "members": members,
        }
