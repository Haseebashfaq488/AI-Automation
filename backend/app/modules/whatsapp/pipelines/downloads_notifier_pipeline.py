import time
from pathlib import Path
from typing import Dict, Any, List

from app.modules.whatsapp.helpers.client import get_client
from app.modules.whatsapp.helpers.validation import resolve_recipient
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_exists, ensure_is_dir


class DownloadsNotifierPipeline:
    """Notify a WhatsApp chat about files that appeared in a folder recently
    (e.g. finished downloads)."""

    name = "downloads_notifier"

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        watch_dir = resolve_path(params["watch_dir"])
        to = resolve_recipient(params["to"])
        since_minutes = float(params.get("since_minutes", 60))
        min_size_mb = float(params.get("min_size_mb", 0))
        ensure_exists(watch_dir)
        ensure_is_dir(watch_dir)

        cutoff = time.time() - since_minutes * 60
        fresh: List[Path] = []
        for p in watch_dir.iterdir():
            if p.is_file() and p.stat().st_mtime >= cutoff and p.stat().st_size >= min_size_mb * 1024 * 1024:
                fresh.append(p)

        if not fresh:
            return {"pipeline": self.name, "success": True, "notified": False,
                    "message": f"No new files in the last {since_minutes:g} minutes."}

        lines = [f"📥 {len(fresh)} new file(s) in {watch_dir.name}:"]
        for p in sorted(fresh, key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
            lines.append(f"  • {p.name} ({p.stat().st_size / 1024 / 1024:.1f} MB)")
        message = "\n".join(lines)

        sent = await get_client().send_message(to, message)
        return {"pipeline": self.name, "success": True, "notified": True,
                "files": [p.name for p in fresh], "to": sent.get("to", to), "message": message}
