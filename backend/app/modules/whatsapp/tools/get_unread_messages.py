from typing import Dict, Any, List
from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client


class GetUnreadMessagesTool(BaseTool):
    """Fetch unread WhatsApp chats and their latest incoming messages."""

    name = "get_unread_messages"
    description = (
        "Get all unread WhatsApp chats and their unread messages, including sender names, "
        "group information, unread counts, and message snippets."
    )
    risk = RiskLevel.LOW

    input_schema = {
        "type": "object",
        "properties": {
            "chat_limit": {
                "type": "integer",
                "default": 30,
                "description": "Maximum number of recent chats to inspect for unread messages",
            },
            "messages_per_chat": {
                "type": "integer",
                "default": 5,
                "description": "Maximum messages to retrieve per unread chat",
            },
        },
        "required": [],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        chat_limit = int(params.get("chat_limit", 30))
        per_chat = min(int(params.get("messages_per_chat", 5)), 15)

        client = get_client()
        chats = await client.list_chats(limit=chat_limit)
        unread_chats = [c for c in chats if c.get("unread", 0) > 0]

        if not unread_chats:
            return {
                "unread_chat_count": 0,
                "total_unread_messages": 0,
                "chats": [],
                "summary": "You have no unread WhatsApp messages. All caught up! ✅",
            }

        detailed_chats: List[Dict[str, Any]] = []
        summary_lines: List[str] = []
        total_unread = 0

        for chat in unread_chats:
            chat_id = chat.get("id") or chat.get("name")
            chat_name = chat.get("name") or chat_id
            unread_count = chat.get("unread", 0)
            total_unread += unread_count
            is_group = chat.get("isGroup", False)
            timestamp = chat.get("timestamp")

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

                # Extract incoming unread messages
                incoming = [m for m in messages if not m.get("fromMe")]
                msg_lines = []
                for m in (incoming[-per_chat:] if incoming else messages[-per_chat:]):
                    author = m.get("author") or m.get("from") or chat_name
                    body = m.get("body") or ("[Media / Attachment]" if m.get("hasMedia") else "")
                    time_val = m.get("timestamp") or ""
                    time_part = f" ({time_val})" if time_val else ""
                    msg_lines.append(f"  • {author}{time_part}: {body}")

                header = f"💬 {chat_name} ({unread_count} unread" + (", Group" if is_group else "") + ")"
                summary_lines.append(header + ("\n" + "\n".join(msg_lines) if msg_lines else "  • (No message body)"))
            except Exception as e:
                chat_info["error"] = str(e)
                summary_lines.append(f"💬 {chat_name} ({unread_count} unread) - [Could not load messages: {e}]")

            detailed_chats.append(chat_info)

        summary_text = (
            f"📬 Unread WhatsApp Messages ({total_unread} unread across {len(unread_chats)} chats):\n\n"
            + "\n\n".join(summary_lines)
        )

        return {
            "unread_chat_count": len(unread_chats),
            "total_unread_messages": total_unread,
            "chats": detailed_chats,
            "summary": summary_text,
        }
