import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from app.modules.whatsapp.helpers.client import get_client
from app.modules.whatsapp.helpers.validation import resolve_recipient
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import validate_path

IMAGE_MIMETYPES = ("image/",)


class PhotoBackupPipeline:
    """Download photos from a WhatsApp chat and store them in YYYY/MM folders."""

    name = "photo_backup"

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        chat = resolve_recipient(params["chat"])
        target = resolve_path(params["target_dir"])
        limit = min(int(params.get("limit", 20)), 100)
        validate_path(target)

        data = await get_client().download_media(chat, limit=limit)
        photos = [m for m in data["media"] if m["mimetype"].startswith(IMAGE_MIMETYPES)]
        if not photos:
            return {"pipeline": self.name, "success": True, "saved": [],
                    "message": "No photos found in the scanned messages."}

        saved: List[Dict[str, str]] = []
        if not params.get("dry_run"):
            for item in photos:
                date = datetime.fromtimestamp(item["timestamp"])
                dest_dir = target / str(date.year) / f"{date.month:02d}"
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / item["filename"]
                counter = 1
                while dest.exists():
                    dest = dest_dir / f"{dest.stem}_{counter}{dest.suffix}"
                    counter += 1
                dest.write_bytes(base64.b64decode(item["data"]))
                saved.append({"filename": item["filename"], "path": str(dest)})
        else:
            for item in photos:
                saved.append({"filename": item["filename"], "path": "(dry run)"})

        return {"pipeline": self.name, "success": True, "dry_run": params.get("dry_run", False),
                "count": len(saved), "saved": saved, "target_dir": str(target)}
