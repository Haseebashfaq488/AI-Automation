from typing import Dict, Any, List

from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client
from app.modules.whatsapp.helpers.validation import resolve_recipient


class UnreadDigestSkill(BaseTool):
    """Collect all unread WhatsApp chats and their recent messages into one digest."""

    name = "unread_digest"
    description = ("Summarize all unread WhatsApp chats (who messaged and what they said). "
                   "Optionally send the digest to a chat.")
    risk = RiskLevel.LOW
    category = "skill"

    input_schema = {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "optional — chat to send the digest to"},
            "chat_limit": {"type": "integer", "default": 50},
            "messages_per_chat": {"type": "integer", "default": 3},
        },
        "required": [],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        chat_limit = int(params.get("chat_limit", 50))
        per_chat = min(int(params.get("messages_per_chat", 3)), 10)

        chats = await get_client().list_chats(limit=chat_limit)
        unread = [c for c in chats if c.get("unread", 0) > 0]

        sections: List[str] = []
        for chat in unread:
            try:
                data = await get_client().get_messages(chat["id"], limit=per_chat)
                incoming = [m for m in data["messages"] if not m.get("fromMe")]
                preview = "\n".join(f"  • {(m.get('body') or '[media]')[:120]}" for m in incoming[-per_chat:])
                sections.append(f"🔔 {chat['name']} ({chat['unread']} unread)\n{preview or '  • [no text]'}")
            except Exception:
                sections.append(f"🔔 {chat['name']} ({chat['unread']} unread)\n  • [could not fetch]")

        digest = "📬 Unread digest\n\n" + ("\n\n".join(sections) if sections else "All caught up! ✅")

        result: Dict[str, Any] = {"unread_chats": len(unread), "digest": digest}
        if params.get("to"):
            to = resolve_recipient(params["to"])
            sent = await get_client().send_message(to, digest)
            result["sent"] = True
            result["to"] = sent.get("to", to)
        return result
