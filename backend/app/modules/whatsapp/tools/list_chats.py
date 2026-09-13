from typing import Dict, Any
from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client


class ListChatsTool(BaseTool):
    name = "list_chats"
    description = "List recent WhatsApp chats with unread counts (optionally only unread ones)."
    risk = RiskLevel.LOW

    input_schema = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "default": 50},
            "unread_only": {"type": "boolean", "default": False},
        },
        "required": [],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        limit = int(params.get("limit", 50))
        chats = await get_client().list_chats(limit=limit)
        if params.get("unread_only"):
            chats = [c for c in chats if c.get("unread", 0) > 0]
        return {"count": len(chats), "chats": chats}
