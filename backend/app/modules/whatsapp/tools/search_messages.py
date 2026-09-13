from typing import Dict, Any, List
from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client
from app.modules.whatsapp.helpers.validation import resolve_recipient


class SearchMessagesTool(BaseTool):
    name = "search_messages"
    description = "Search recent messages in a WhatsApp chat for a text (case-insensitive)."
    risk = RiskLevel.LOW

    input_schema = {
        "type": "object",
        "properties": {
            "chat": {"type": "string", "description": "chat name or id"},
            "query": {"type": "string"},
            "limit": {"type": "integer", "description": "how many recent messages to scan", "default": 100},
        },
        "required": ["chat", "query"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        chat = resolve_recipient(params["chat"])
        query = params["query"]
        scan_limit = min(int(params.get("limit", 100)), 100)
        data = await get_client().get_messages(chat, limit=scan_limit)
        needle = query.lower()
        matches: List[Dict[str, Any]] = [
            m for m in data["messages"] if needle in (m.get("body") or "").lower()
        ]
        return {
            "chat": data["chat"],
            "query": query,
            "scanned": len(data["messages"]),
            "match_count": len(matches),
            "matches": matches,
        }
