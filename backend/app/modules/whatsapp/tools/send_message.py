from typing import Dict, Any
from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client
from app.modules.whatsapp.helpers.validation import resolve_recipient


class SendMessageTool(BaseTool):
    name = "send_message"
    description = "Send a WhatsApp text message to a chat (by chat name or phone number)."
    risk = RiskLevel.HIGH

    input_schema = {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "chat name or phone number"},
            "message": {"type": "string"},
            "dry_run": {"type": "boolean", "default": False},
        },
        "required": ["to", "message"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        to = resolve_recipient(params["to"])
        message = params["message"]
        if params.get("dry_run"):
            return {"dry_run": True, "action": f"Would send WhatsApp message to {to}: {message[:100]!r}"}
        result = await get_client().send_message(to, message)
        return {"sent": True, "to": result.get("to", to), "messageId": result.get("messageId")}
