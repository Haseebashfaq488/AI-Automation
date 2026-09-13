from pathlib import Path
from typing import Any, Dict


def verify_exists(path: Path) -> Dict[str, Any]:
    """Return a verification dict confirming existence of the path."""
    return {"exists": path.exists(), "path": str(path)}


def verify_is_file(path: Path) -> Dict[str, Any]:
    return {"is_file": path.is_file(), "path": str(path)}


def verify_is_dir(path: Path) -> Dict[str, Any]:
    return {"is_dir": path.is_dir(), "path": str(path)}


def verify_content(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise ValueError("Can only verify content of a file")
    with path.open("r", encoding="utf-8") as f:
        content = f.read()
    return {"size": path.stat().st_size, "content_preview": content[:200], "path": str(path)}
