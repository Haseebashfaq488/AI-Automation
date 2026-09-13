import shutil
from pathlib import Path
from typing import Dict, Any, List

from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_exists, ensure_is_dir, validate_path


class BackupDocumentsPipeline:
    """One-way incremental backup: copy files that are new or newer than the backup copy."""

    name = "backup_documents"

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        src = resolve_path(params["source_dir"])
        backup = resolve_path(params["backup_dir"])
        dry = params.get("dry_run", False)
        ensure_exists(src)
        ensure_is_dir(src)
        validate_path(src)
        validate_path(backup)

        copied: List[str] = []
        skipped = 0
        for f in sorted(p for p in src.rglob("*") if p.is_file()):
            rel = f.relative_to(src)
            dest = backup / rel
            if dest.exists() and dest.stat().st_mtime >= f.stat().st_mtime:
                skipped += 1
                continue
            copied.append(str(f))
            if not dry:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)

        return {
            "pipeline": self.name,
            "success": True,
            "dry_run": dry,
            "source": str(src),
            "backup_dir": str(backup),
            "copied": copied,
            "copied_count": len(copied),
            "skipped_count": skipped,
        }
