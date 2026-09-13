from typing import Dict, Any, List
import shutil
from pathlib import Path
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import validate_path


class OrganizeDownloadsSkill(BaseTool):
    """Organize files in a download directory into subfolders by file extension.

    Parameters
    ----------
    source_dir: str
        Path to the directory containing the files to organize.
    target_dir: str (optional)
        Destination base directory. If omitted, files are organized in-place.
    """

    name = "organize_downloads"
    description = "Organize files in a directory into subfolders based on file extensions."
    risk = RiskLevel.LOW
    category = "skill"
    input_schema = {
        "type": "object",
        "properties": {
            "source_dir": {"type": "string"},
            "target_dir": {"type": "string"},
        },
        "required": ["source_dir"],
    }

    def _ensure_dir(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        src = resolve_path(params["source_dir"])
        tgt = resolve_path(params.get("target_dir", str(src)))
        if not src.is_dir():
            raise NotADirectoryError(f"Source directory does not exist: {src}")
        validate_path(src)
        validate_path(tgt)
        self._ensure_dir(tgt)
        moved: List[Dict[str, str]] = []
        for item in src.iterdir():
            if item.is_file():
                ext = item.suffix.lower().lstrip(".") or "no_extension"
                dest_dir = tgt / ext
                self._ensure_dir(dest_dir)
                dest_path = dest_dir / item.name
                shutil.move(str(item), str(dest_path))
                moved.append({"source": str(item), "destination": str(dest_path)})
        return {"organized": True, "moved": moved}
