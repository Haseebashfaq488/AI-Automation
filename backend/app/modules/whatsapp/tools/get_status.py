from typing import Dict, Any
from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client
from app.modules.whatsapp.helpers import session


class GetStatusTool(BaseTool):
    name = "whatsapp_status"
    description = "Check the WhatsApp connection status (disconnected / waiting for QR / ready)."
    risk = RiskLevel.LOW

    input_schema = {"type": "object", "properties": {}, "required": []}

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        status = await get_client().status()
        return {
            "state": status.get("state"),
            "description": session.describe(status.get("state", "disconnected")),
            "connected": status.get("state") == session.READY,
            "pushname": status.get("pushname"),
        }
