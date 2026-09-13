from typing import Dict, Any
from pathlib import Path
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_exists, ensure_is_file


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the contents of a text file (UTF-8)."
    risk = RiskLevel.LOW

    # Safety cap to avoid reading huge/binary files into memory (10 MB).
    MAX_READ_BYTES = 10 * 1024 * 1024

    input_schema = {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_path(params["path"])
        ensure_exists(path)
        ensure_is_file(path)
        if path.stat().st_size > self.MAX_READ_BYTES:
            raise ValueError(
                f"File too large to read ({path.stat().st_size} bytes > {self.MAX_READ_BYTES} bytes): {path}"
            )
        with path.open("r", encoding="utf-8") as f:
            content = f.read()
        return {"path": str(path), "content": content}
