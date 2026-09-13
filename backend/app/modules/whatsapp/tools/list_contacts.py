from typing import Dict, Any
from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client


class ListContactsTool(BaseTool):
    name = "list_contacts"
    description = "List WhatsApp contacts, optionally filtered by name or number."
    risk = RiskLevel.LOW

    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "optional name/number filter"},
        },
        "required": [],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        contacts = await get_client().contacts(query=params.get("query"))
        return {"count": len(contacts), "contacts": contacts}
