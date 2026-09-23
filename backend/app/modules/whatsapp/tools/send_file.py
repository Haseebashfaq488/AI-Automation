from pathlib import Path
from typing import Dict, Any
from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client
from app.modules.whatsapp.helpers.validation import resolve_recipient
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_exists, ensure_is_file, validate_path


class SendFileTool(BaseTool):
    name = "send_file"
    description = "Send a local file (document, image, video…) to a WhatsApp chat, with an optional caption."
    risk = RiskLevel.HIGH

    input_schema = {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "chat name or phone number"},
            "path": {"type": "string", "description": "absolute path of the local file"},
            "caption": {"type": "string"},
            "dry_run": {"type": "boolean", "default": False},
        },
        "required": ["to", "path"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        to = resolve_recipient(params["to"])
        raw_path = str(params.get("path", "")).strip()

        # Fallback if path parameter was left empty or as an unresolved placeholder
        if not raw_path or raw_path in ("{worker.artifact}", "{worker.artifact_path}", "None"):
            workspace_dir = Path("D:/workspace")
            if workspace_dir.is_dir():
                ws_files = [f for f in workspace_dir.iterdir() if f.is_file() and not f.name.startswith(".")]
                if ws_files:
                    ws_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                    raw_path = str(ws_files[0])

        path = resolve_path(raw_path)
        caption = params.get("caption")
        ensure_exists(path)
        ensure_is_file(path)
        validate_path(path)
        if params.get("dry_run"):
            return {"dry_run": True, "action": f"Would send file {path} to {to}"}
        result = await get_client().send_file(to, str(path), caption)
        return {
            "sent": True,
            "to": result.get("to", to),
            "filename": path.name,
            "messageId": result.get("messageId"),
        }

