from typing import Dict, Any
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import validate_path


class AppendFileTool(BaseTool):
    name = "append_file"
    description = "Append text content to the end of a file (creates the file if missing)."
    risk = RiskLevel.MEDIUM

    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
            "dry_run": {"type": "boolean", "default": False},
        },
        "required": ["path", "content"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_path(params["path"])
        content = params["content"]
        validate_path(path)
        dry = params.get("dry_run", False)
        if dry:
            return {"dry_run": True, "action": f"Would append {len(content)} chars to {path}"}
        path.parent.mkdir(parents=True, exist_ok=True)
        # newline="" prevents Windows translating "\n" to "\r\n" — store exact content.
        with path.open("a", encoding="utf-8", newline="") as f:
            f.write(content)
        stat = path.stat()
        return {
            "appended": True,
            "path": str(path),
            "chars_appended": len(content),
            "size": stat.st_size,
        }
