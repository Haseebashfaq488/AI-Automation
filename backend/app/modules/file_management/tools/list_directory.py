from pathlib import Path
from typing import Dict, Any, List
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_is_dir


class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "List entries in a directory (non‑recursive)."
    risk = RiskLevel.LOW
    input_schema = {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_path(params["path"])
        ensure_is_dir(path)
        entries: List[Dict[str, Any]] = []
        for entry in path.iterdir():
            entries.append({
                "name": entry.name,
                "is_file": entry.is_file(),
                "is_dir": entry.is_dir(),
                "size": entry.stat().st_size if entry.is_file() else None,
            })
        return {"path": str(path), "entries": entries}
