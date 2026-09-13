import hashlib
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple

from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_exists, ensure_is_dir, validate_path


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class DedupeFolderPipeline:
    """Find duplicate files (by size + SHA-256) and move extras into a review folder."""

    name = "dedupe_folder"

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        src = resolve_path(params["source_dir"])
        review_dir = resolve_path(params.get("review_dir") or str(src / "duplicates"))
        recursive = params.get("recursive", False)
        dry = params.get("dry_run", False)
        ensure_exists(src)
        ensure_is_dir(src)
        validate_path(src)
        validate_path(review_dir)

        candidates = src.rglob("*") if recursive else src.iterdir()
        files = sorted((p for p in candidates if p.is_file()), key=lambda p: p.name)

        groups: Dict[Tuple[int, str], List[Path]] = {}
        for f in files:
            key = (f.stat().st_size, _file_hash(f))
            groups.setdefault(key, []).append(f)

        duplicates: List[Dict[str, str]] = []
        kept: List[str] = []
        for key, group in groups.items():
            kept.append(str(group[0]))
            for extra in group[1:]:
                # ensure a unique name inside the review folder
                dest = review_dir / extra.name
                counter = 1
                while dest.exists():
                    dest = review_dir / f"{extra.stem}_{counter}{extra.suffix}"
                    counter += 1
                duplicates.append({"source": str(extra), "destination": str(dest)})

        if dry:
            return {"pipeline": self.name, "success": True, "dry_run": True,
                    "duplicates": duplicates, "kept": kept}

        review_dir.mkdir(parents=True, exist_ok=True)
        moved: List[Dict[str, str]] = []
        for item in duplicates:
            shutil.move(item["source"], item["destination"])
            moved.append(item)
        return {
            "pipeline": self.name,
            "success": True,
            "duplicates": moved,
            "duplicate_count": len(moved),
            "kept": kept,
        }
