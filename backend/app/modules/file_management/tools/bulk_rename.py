from typing import Dict, Any, List
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_exists, ensure_is_dir, validate_path


class BulkRenameTool(BaseTool):
    name = "bulk_rename"
    description = ("Rename all files in a folder using a pattern. Use '#' characters as a "
                   "zero-padded counter, e.g. 'photo_###' -> photo_001, photo_002, ... "
                   "Extensions are preserved.")
    risk = RiskLevel.MEDIUM

    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "folder containing the files"},
            "pattern": {"type": "string", "description": "new name pattern, use # for the counter"},
            "extension": {"type": "string", "description": "optional, only rename files with this extension (e.g. .jpg)"},
            "start_index": {"type": "integer", "default": 1},
            "dry_run": {"type": "boolean", "default": False},
        },
        "required": ["path", "pattern"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        folder = resolve_path(params["path"])
        pattern = params["pattern"]
        extension = params.get("extension")
        start_index = int(params.get("start_index", 1))
        dry = params.get("dry_run", False)
        ensure_exists(folder)
        ensure_is_dir(folder)
        validate_path(folder)

        if extension and not extension.startswith("."):
            extension = "." + extension

        files = sorted(
            (p for p in folder.iterdir() if p.is_file() and (extension is None or p.suffix.lower() == extension.lower())),
            key=lambda p: p.name,
        )
        if not files:
            return {"renamed": 0, "renames": [], "message": "No matching files found."}

        hashes = pattern.count("#")
        planned: Dict[Any, str] = {}
        conflicts: List[str] = []
        existing_names = {p.name for p in folder.iterdir() if p.is_file()}
        for i, f in enumerate(files, start=start_index):
            if hashes:
                new_name = pattern.replace("#" * hashes, str(i).zfill(hashes))
            else:
                new_name = f"{pattern}_{i}"
            new_name += f.suffix
            planned[f] = new_name

        renames: List[Dict[str, str]] = []
        for f, new_name in planned.items():
            if new_name != f.name and new_name in existing_names and new_name not in {v for v in planned.values()}:
                conflicts.append(f.name)
                continue
            renames.append({"source": f.name, "destination": new_name})

        if dry:
            return {"dry_run": True, "renamed": len(renames), "renames": renames, "conflicts": conflicts}

        # apply renames (skipping conflicts)
        applied = 0
        for r in renames:
            src = folder / r["source"]
            dst = folder / r["destination"]
            if r["source"] in conflicts:
                continue
            src.rename(dst)
            applied += 1
        return {"renamed": applied, "renames": renames, "conflicts": conflicts}
