from typing import Dict, Any
from pathlib import Path
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_exists


class MetadataTool(BaseTool):
    name = "metadata"
    description = "Return basic metadata for a file or directory."
    risk = RiskLevel.LOW
    input_schema = {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_path(params["path"])
        # Validate path exists
        ensure_exists(path)
        stat = path.stat()
        return {
            "path": str(path),
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "size": stat.st_size,
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
            "extension": path.suffix,
        }
