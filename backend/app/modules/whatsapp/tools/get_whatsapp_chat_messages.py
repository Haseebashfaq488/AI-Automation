from typing import Dict, Any, List
from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client
from app.modules.whatsapp.helpers.validation import resolve_recipient


class GetWhatsAppChatMessagesTool(BaseTool):
    """Retrieve messages from a specific WhatsApp chat or group within the 3-day activity window."""

    name = "get_whatsapp_chat_messages"
    description = (
        "Fetch timestamped messages from a specific WhatsApp contact or group name (e.g. 'Zahida Ashfaq', 'Bois 🔥'), "
        "including messages from Today, Yesterday, and Day Before Yesterday."
    )
    risk = RiskLevel.LOW

    input_schema = {
        "type": "object",
        "properties": {
            "chat": {
                "type": "string",
                "description": "The exact or partial contact name, group name, or phone number to open",
            },
            "limit": {
                "type": "integer",
                "default": 30,
                "description": "Maximum number of recent messages to fetch",
            },
            "days": {
                "type": "integer",
                "default": 3,
                "description": "Days to retrieve (e.g. 3 for Today, Yesterday, Day Before Yesterday)",
            },
        },
        "required": ["chat"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        chat_query = resolve_recipient(params["chat"])
        limit = min(int(params.get("limit", 30)), 100)
        days = int(params.get("days", 3))

        client = get_client()
        data = await client.get_messages(chat_query, limit=limit, days=days)
        chat_meta = data.get("chat", {})
        messages = data.get("messages", [])

        if not messages:
            return {
                "chat": chat_meta,
                "count": 0,
                "messages": [],
                "summary": f"No recent messages found for chat '{chat_query}' within the last {days} days.",
            }

        # Group messages by date bucket (Today, Yesterday, Day Before Yesterday / date)
        by_date: Dict[str, List[Dict[str, Any]]] = {}
        for m in messages:
            d_key = m.get("date") or "Today"
            by_date.setdefault(d_key, []).append(m)

        summary_sections = []
        for d_key, msgs in by_date.items():
            lines = []
            for m in msgs:
                from_me = m.get("fromMe", False)
                author = "You" if from_me else (m.get("author") or m.get("from") or chat_meta.get("name") or chat_query)
                time_val = m.get("time") or m.get("timestamp") or ""
                body = m.get("body") or ("[Media / Attachment]" if m.get("hasMedia") else "")
                lines.append(f"  [{time_val}] {author}: {body}")
            summary_sections.append(f"📅 **{d_key}**:\n" + "\n".join(lines))

        full_summary = f"💬 **Chat: {chat_meta.get('name', chat_query)}** ({len(messages)} messages):\n\n" + "\n\n".join(summary_sections)

        return {
            "chat": chat_meta,
            "count": len(messages),
            "messages": messages,
            "grouped_by_date": by_date,
            "summary": full_summary,
        }
