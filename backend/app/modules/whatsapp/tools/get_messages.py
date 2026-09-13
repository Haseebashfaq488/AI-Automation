from typing import Dict, Any
from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client
from app.modules.whatsapp.helpers.validation import resolve_recipient


class GetMessagesTool(BaseTool):
    name = "get_messages"
    description = "Fetch the most recent messages from a WhatsApp chat."
    risk = RiskLevel.LOW

    input_schema = {
        "type": "object",
        "properties": {
            "chat": {"type": "string", "description": "chat name or id"},
            "limit": {"type": "integer", "default": 20},
        },
        "required": ["chat"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        chat = resolve_recipient(params["chat"])
        limit = min(int(params.get("limit", 20)), 100)
        data = await get_client().get_messages(chat, limit=limit)
        return {
            "chat": data["chat"],
            "count": len(data["messages"]),
            "messages": data["messages"],
        }
