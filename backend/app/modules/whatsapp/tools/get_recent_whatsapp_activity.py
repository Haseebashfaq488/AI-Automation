from typing import Dict, Any, List
from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client


class GetRecentWhatsAppActivityTool(BaseTool):
    """Retrieve recent WhatsApp chats and messages from the last 24 hours."""

    name = "get_recent_whatsapp_activity"
    description = (
        "Get recent WhatsApp conversations and messages from the last 24 hours, "
        "including incoming and outgoing messages, chat participants, and timestamps."
    )
    risk = RiskLevel.LOW

    input_schema = {
        "type": "object",
        "properties": {
            "chat_limit": {
                "type": "integer",
                "default": 10,
                "description": "Number of recent active chats to inspect",
            },
            "messages_per_chat": {
                "type": "integer",
                "default": 5,
                "description": "Number of recent messages to fetch per active chat",
            },
        },
        "required": [],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        chat_limit = min(int(params.get("chat_limit", 10)), 25)
        per_chat = min(int(params.get("messages_per_chat", 5)), 15)

        client = get_client()
        chats = await client.list_chats(limit=chat_limit)

        if not chats:
            return {
                "chat_count": 0,
                "chats": [],
                "summary": "No recent WhatsApp chats or activity found in the last 24 hours.",
            }

        detailed_chats: List[Dict[str, Any]] = []
        summary_sections: List[str] = []

        for chat in chats:
            chat_id = chat.get("id") or chat.get("name")
            chat_name = chat.get("name") or chat_id
            unread_count = chat.get("unread", 0)
            is_group = chat.get("isGroup", False)
            timestamp = chat.get("timestamp") or "Recent"

            chat_info = {
                "chat_id": chat_id,
                "name": chat_name,
                "unread_count": unread_count,
                "is_group": is_group,
                "timestamp": timestamp,
                "preview": chat.get("preview", ""),
                "messages": [],
            }

            try:
                msg_data = await client.get_messages(chat_id, limit=per_chat)
                messages = msg_data.get("messages", [])
                chat_info["messages"] = messages

                msg_lines = []
                for m in messages[-per_chat:]:
                    from_me = m.get("fromMe", False)
                    author = "You" if from_me else (m.get("author") or m.get("from") or chat_name)
                    body = m.get("body") or ("[Media / Attachment]" if m.get("hasMedia") else "")
                    time_val = m.get("timestamp") or ""
                    time_part = f" ({time_val})" if time_val else ""
                    msg_lines.append(f"  • {author}{time_part}: {body}")

                badge = f" [{unread_count} unread]" if unread_count > 0 else ""
                group_tag = " (Group)" if is_group else ""
                header = f"💬 {chat_name}{group_tag} — {timestamp}{badge}"
                summary_sections.append(
                    header + ("\n" + "\n".join(msg_lines) if msg_lines else "  • (No message body)")
                )
            except Exception as e:
                chat_info["error"] = str(e)
                summary_sections.append(
                    f"💬 {chat_name} — {timestamp}\n  • Latest preview: {chat.get('preview', '')}"
                )

            detailed_chats.append(chat_info)

        summary_text = (
            f"📱 WhatsApp Recent Activity (Last 24 Hours — {len(detailed_chats)} Active Chats):\n\n"
            + "\n\n".join(summary_sections)
        )

        return {
            "chat_count": len(detailed_chats),
            "chats": detailed_chats,
            "summary": summary_text,
        }
