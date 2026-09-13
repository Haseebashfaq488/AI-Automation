import zipfile
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Dict, Any, List

from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_exists, ensure_is_dir, validate_path


class ArchiveOldFilesPipeline:
    """Zip files that have not been modified in the last N months, then remove the originals."""

    name = "archive_old_files"

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        src = resolve_path(params["source_dir"])
        months = int(params.get("older_than_months", 12))
        archive_dir = resolve_path(params.get("archive_dir") or str(src / "archives"))
        dry = params.get("dry_run", False)
        ensure_exists(src)
        ensure_is_dir(src)
        validate_path(src)
        validate_path(archive_dir)

        cutoff = datetime.now(UTC).timestamp() - timedelta(days=months * 30).total_seconds()
        old_files = [p for p in sorted(src.iterdir()) if p.is_file() and p.stat().st_mtime < cutoff]

        if not old_files:
            return {"pipeline": self.name, "success": True, "archived": [],
                    "message": "No files older than the cutoff.", "zip_path": None}

        stamp = datetime.now(UTC).strftime("%Y%m%d")
        zip_path = archive_dir / f"archive_{stamp}.zip"
        counter = 1
        while zip_path.exists():
            zip_path = archive_dir / f"archive_{stamp}_{counter}.zip"
            counter += 1

        if dry:
            return {"pipeline": self.name, "success": True, "dry_run": True,
                    "zip_path": str(zip_path), "archived": [str(f) for f in old_files]}

        archive_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in old_files:
                zf.write(f, arcname=f.name)
        # remove originals only after a valid archive was written
        archived: List[str] = []
        for f in old_files:
            f.unlink()
            archived.append(str(f))
        return {
            "pipeline": self.name,
            "success": True,
            "zip_path": str(zip_path),
            "archived": archived,
            "archived_count": len(archived),
            "size_bytes": zip_path.stat().st_size,
        }
