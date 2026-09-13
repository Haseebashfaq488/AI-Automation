from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client
from app.modules.whatsapp.helpers.validation import resolve_recipient
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_exists


class SendReportSkill(BaseTool):
    """Summarize a file or folder and send the summary as a WhatsApp message."""

    name = "send_report"
    description = "Summarize a file or folder (name, size, contents preview) and send the report to a WhatsApp chat."
    risk = RiskLevel.MEDIUM
    category = "skill"

    input_schema = {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "chat name or phone number"},
            "path": {"type": "string", "description": "file or folder to summarize"},
            "max_entries": {"type": "integer", "default": 15},
        },
        "required": ["to", "path"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        to = resolve_recipient(params["to"])
        path = resolve_path(params["path"])
        ensure_exists(path)
        max_entries = int(params.get("max_entries", 15))

        lines = [f"📋 Report: {path.name}", f"Path: {path}"]
        if path.is_file():
            stat = path.stat()
            lines.append(f"Type: file ({path.suffix or 'no extension'})")
            lines.append(f"Size: {stat.st_size} bytes")
            lines.append(f"Modified: {datetime.fromtimestamp(stat.st_mtime):%Y-%m-%d %H:%M}")
            if path.suffix.lower() in {".txt", ".md", ".log", ".json", ".csv"} and stat.st_size < 1024 * 1024:
                try:
                    preview = path.read_text(encoding="utf-8", errors="ignore")[:500]
                    lines.append(f"Preview:\n{preview}")
                except OSError:
                    pass
        else:
            entries = sorted(path.iterdir())
            files = [e for e in entries if e.is_file()]
            dirs = [e for e in entries if e.is_dir()]
            lines.append(f"Type: folder — {len(files)} files, {len(dirs)} subfolders")
            for e in entries[:max_entries]:
                lines.append(f"  {'📁' if e.is_dir() else '📄'} {e.name}")
            if len(entries) > max_entries:
                lines.append(f"  … and {len(entries) - max_entries} more")

        report = "\n".join(lines)
        result = await get_client().send_message(to, report)
        return {"sent": True, "to": result.get("to", to), "report": report}
