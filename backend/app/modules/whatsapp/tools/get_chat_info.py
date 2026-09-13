from typing import Dict, Any
from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client
from app.modules.whatsapp.helpers.validation import resolve_recipient


class GetChatInfoTool(BaseTool):
    name = "get_chat_info"
    description = "Get info about a WhatsApp chat (name, unread count, group participants, pinned state)."
    risk = RiskLevel.LOW

    input_schema = {
        "type": "object",
        "properties": {
            "chat": {"type": "string", "description": "chat name or id"},
        },
        "required": ["chat"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        chat = resolve_recipient(params["chat"])
        return await get_client().chat_info(chat)
