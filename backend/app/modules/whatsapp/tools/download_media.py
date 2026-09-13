import base64
from pathlib import Path
from typing import Dict, Any, List
from app.core.tool import BaseTool, RiskLevel
from app.modules.whatsapp.helpers.client import get_client
from app.modules.whatsapp.helpers.paths import MEDIA_ROOT
from app.modules.whatsapp.helpers.validation import resolve_recipient


class DownloadMediaTool(BaseTool):
    name = "download_media"
    description = "Download media (photos, documents, voice notes) from a WhatsApp chat to a local folder."
    risk = RiskLevel.MEDIUM

    input_schema = {
        "type": "object",
        "properties": {
            "chat": {"type": "string", "description": "chat name or id"},
            "destination": {"type": "string", "description": "local folder (default: backend/whatsapp_media)"},
            "limit": {"type": "integer", "default": 20},
        },
        "required": ["chat"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        chat = resolve_recipient(params["chat"])
        dest = Path(params["destination"]).expanduser().resolve() if params.get("destination") else MEDIA_ROOT
        limit = min(int(params.get("limit", 20)), 100)
        data = await get_client().download_media(chat, limit=limit)
        dest.mkdir(parents=True, exist_ok=True)
        saved: List[Dict[str, str]] = []
        for item in data["media"]:
            target = dest / item["filename"]
            counter = 1
            while target.exists():
                target = dest / f"{target.stem}_{counter}{target.suffix}"
                counter += 1
            target.write_bytes(base64.b64decode(item["data"]))
            saved.append({"filename": item["filename"], "mimetype": item["mimetype"], "path": str(target)})
        return {"chat": data["chat"], "downloaded": len(saved), "files": saved, "destination": str(dest)}
