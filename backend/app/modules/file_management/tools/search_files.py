from typing import Dict, Any, List
from pathlib import Path
from fnmatch import fnmatch
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import validate_path, ensure_exists, ensure_is_dir


class SearchFilesTool(BaseTool):
    name = "search_files"
    description = "Search for files matching a pattern within a directory."
    risk = RiskLevel.LOW
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "pattern": {"type": "string"},
            "recursive": {"type": "boolean", "default": False},
        },
        "required": ["path", "pattern"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        base_path = resolve_path(params["path"])
        pattern = params["pattern"]
        recursive = params.get("recursive", False)
        ensure_exists(base_path)
        ensure_is_dir(base_path)
        matches: List[str] = []
        if recursive:
            for p in base_path.rglob("*"):
                if p.is_file() and fnmatch(p.name, pattern):
                    matches.append(str(p))
        else:
            for p in base_path.iterdir():
                if p.is_file() and fnmatch(p.name, pattern):
                    matches.append(str(p))
        return {"path": str(base_path), "pattern": pattern, "recursive": recursive, "matches": matches}
