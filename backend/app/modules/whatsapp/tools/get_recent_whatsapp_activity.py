from typing import Dict, Any, List
from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client


class GetRecentWhatsAppActivityTool(BaseTool):
    """Retrieve WhatsApp conversations and messages from Today, Yesterday, and Day Before Yesterday."""

    name = "get_recent_whatsapp_activity"
    description = (
        "Scan WhatsApp chats active within the last 3 days (Today, Yesterday, Day Before Yesterday), "
        "and retrieve detailed timestamped dialogues and summaries grouped per user/group."
    )
    risk = RiskLevel.LOW

    input_schema = {
        "type": "object",
        "properties": {
            "chat_limit": {
                "type": "integer",
                "default": 8,
                "description": "Number of active 3-day chats to inspect and scrape",
            },
            "messages_per_chat": {
                "type": "integer",
                "default": 10,
                "description": "Number of recent messages to fetch per active chat",
            },
            "days": {
                "type": "integer",
                "default": 3,
                "description": "Activity filter window (default 3: Today, Yesterday, Day Before Yesterday)",
            },
        },
        "required": [],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        chat_limit = min(int(params.get("chat_limit", 8)), 20)
        per_chat = min(int(params.get("messages_per_chat", 10)), 30)
        days = int(params.get("days", 3))

        client = get_client()
        conversations = await client.get_recent_conversations(
            chat_limit=chat_limit,
            messages_per_chat=per_chat,
            days=days,
        )

        if not conversations:
            return {
                "chat_count": 0,
                "conversations": [],
                "summary": f"No active WhatsApp chats found in the {days}-day window (Today, Yesterday, Day Before Yesterday).",
            }

        chat_summaries: List[str] = []
        structured_chats: List[Dict[str, Any]] = []

        for c in conversations:
            chat_name = c.get("name") or c.get("id")
            activity_bucket = c.get("activity_bucket") or "today"
            timestamp = c.get("timestamp") or "Recent"
            unread = c.get("unread", 0)
            is_group = c.get("isGroup", False)
            messages = c.get("messages", [])

            # Categorize messages by date
            by_date: Dict[str, List[Dict[str, Any]]] = {}
            for m in messages:
                d_key = m.get("date") or "Today"
                by_date.setdefault(d_key, []).append(m)

            msg_lines: List[str] = []
            for d_key, d_msgs in by_date.items():
                msg_lines.append(f"  📅 {d_key}:")
                for m in d_msgs:
                    from_me = m.get("fromMe", False)
                    author = "You" if from_me else (m.get("author") or m.get("from") or chat_name)
                    time_val = m.get("time") or m.get("timestamp") or ""
                    time_str = f" [{time_val}]" if time_val else ""
                    body = m.get("body") or ("[Media / Attachment]" if m.get("hasMedia") else "")
                    msg_lines.append(f"    • {author}{time_str}: {body}")

            badge = f" ({unread} unread)" if unread > 0 else ""
            group_tag = " (Group)" if is_group else ""
            header = f"💬 **{chat_name}**{group_tag} — Activity: *{activity_bucket.capitalize()} ({timestamp})*{badge}"
            
            chat_section = header + ("\n" + "\n".join(msg_lines) if msg_lines else f"\n    • Latest preview: {c.get('preview', '(empty)')}")
            chat_summaries.append(chat_section)

            structured_chats.append({
                "chat_id": c.get("id"),
                "name": chat_name,
                "is_group": is_group,
                "unread": unread,
                "timestamp": timestamp,
                "activity_bucket": activity_bucket,
                "preview": c.get("preview", ""),
                "messages": messages,
                "grouped_by_date": by_date,
            })

        overall_summary = (
            f"📱 **WhatsApp Recent Activity ({days}-Day Horizon: Today, Yesterday, Day Before Yesterday)**\n"
            f"Found {len(structured_chats)} active conversations:\n\n"
            + "\n\n".join(chat_summaries)
        )

        return {
            "chat_count": len(structured_chats),
            "conversations": structured_chats,
            "summary": overall_summary,
        }
