from typing import Dict, Any
from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client
from app.modules.whatsapp.helpers import session
from app.modules.whatsapp.helpers.validation import validate_chat_action


class ManageChatTool(BaseTool):
    name = "manage_chat"
    description = ("Manage a WhatsApp chat: pin, unpin, mute, unmute, archive, unarchive, "
                   "mark_read, or clear its messages.")
    risk = RiskLevel.MEDIUM

    input_schema = {
        "type": "object",
        "properties": {
            "chat": {"type": "string", "description": "chat name or id"},
            "action": {"type": "string", "description": "pin|unpin|mute|unmute|archive|unarchive|mark_read|clear"},
            "dry_run": {"type": "boolean", "default": False},
        },
        "required": ["chat", "action"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        chat = params["chat"]
        action = validate_chat_action(params["action"])
        if params.get("dry_run"):
            return {"dry_run": True, "action": f"Would {action} chat {chat}"}
        result = await get_client().chat_action(chat, action)
        return {"ok": True, "chat": result.get("chat", chat), "action": action}
