import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_exists, ensure_is_dir, validate_path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".heic"}


class OrganizePhotosPipeline:
    """Sort image files into YYYY/MM subfolders based on their modified date."""

    name = "organize_photos"

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        src = resolve_path(params["source_dir"])
        tgt = resolve_path(params.get("target_dir") or str(src))
        dry = params.get("dry_run", False)
        ensure_exists(src)
        ensure_is_dir(src)
        validate_path(src)
        validate_path(tgt)

        images = [p for p in sorted(src.iterdir())
                  if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
        planned: List[Dict[str, str]] = []
        for img in images:
            date = datetime.fromtimestamp(img.stat().st_mtime)
            dest_dir = tgt / str(date.year) / f"{date.month:02d}"
            planned.append({"source": str(img), "destination": str(dest_dir / img.name)})

        if dry:
            return {"pipeline": self.name, "success": True, "dry_run": True, "moved": planned}

        moved: List[Dict[str, str]] = []
        for item in planned:
            s, d = Path(item["source"]), Path(item["destination"])
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(s), str(d))
            moved.append(item)
        return {"pipeline": self.name, "success": True, "moved": moved, "count": len(moved)}
