from typing import Dict, Any
from pathlib import Path
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import validate_path
from app.modules.file_management.helpers.verification import verify_content


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write text content to a file (creates if missing)."
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
        validate_path(path)
        content = params["content"]
        dry = params.get("dry_run", False)
        if dry:
            return {"dry_run": True, "action": f"Would write to file {path}"}
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        # newline="" prevents Windows translating "\n" to "\r\n" — store exact content.
        with path.open("w", encoding="utf-8", newline="") as f:
            f.write(content)
        return {"written": True, "path": str(path), **verify_content(path)}
