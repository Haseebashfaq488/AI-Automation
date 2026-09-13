from typing import Dict, Any

from app.modules.whatsapp.skills.unread_digest import UnreadDigestSkill


class DailyDigestPipeline:
    """Run the unread digest and send it to the given chat (run on a schedule or on demand)."""

    name = "daily_digest"

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        to = params.get("to")
        if not to:
            raise ValueError("'to' (destination chat) is required for daily_digest")
        result = await UnreadDigestSkill().execute({
            "to": to,
            "chat_limit": int(params.get("chat_limit", 50)),
            "messages_per_chat": int(params.get("messages_per_chat", 3)),
        })
        return {"pipeline": self.name, "success": True, **result}
