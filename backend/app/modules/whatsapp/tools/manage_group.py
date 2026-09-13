from typing import Dict, Any, List
from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client
from app.modules.whatsapp.helpers.validation import resolve_recipient, validate_group_action


class ManageGroupTool(BaseTool):
    name = "manage_group"
    description = ("Manage WhatsApp groups: create a group, or add/remove/promote/demote "
                   "participants, or leave a group.")
    risk = RiskLevel.HIGH

    input_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "description": "create|add|remove|promote|demote|leave"},
            "name": {"type": "string", "description": "group name (for create)"},
            "chat": {"type": "string", "description": "group name or id (not needed for create)"},
            "participants": {"type": "array", "items": {"type": "string"},
                             "description": "phone numbers or contact ids"},
            "dry_run": {"type": "boolean", "default": False},
        },
        "required": ["action"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        action = validate_group_action(params["action"])
        chat = resolve_recipient(params["chat"]) if params.get("chat") else None
        name = params.get("name")
        participants: List[str] = [resolve_recipient(p) for p in params.get("participants", [])]
        if params.get("dry_run"):
            return {"dry_run": True, "action": f"Would {action} group {name or chat or ''}".strip()}
        result = await get_client().group_action(action, chat=chat, name=name, participants=participants)
        return {"ok": True, "action": action, **result}
