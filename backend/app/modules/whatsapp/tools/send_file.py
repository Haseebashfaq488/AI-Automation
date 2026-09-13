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
        path = resolve_path(params["path"])
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
