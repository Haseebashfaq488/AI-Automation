from pathlib import Path
from typing import Union

# Base directory for the Jarvis backend (project root)
BASE_DIR = Path(__file__).resolve().parents[4]  # backend
WORKSPACE_DIR = Path(r"D:\workspace")


def resolve_path(path_str: str) -> Path:
    """Resolve a user-provided path string to an absolute Path.

    - Rejects empty strings.
    - Expands ``~`` to the user home directory.
    - Resolves relative paths checking ``WORKSPACE_DIR`` first, then ``BASE_DIR``.
    - Returns a normalized absolute ``Path``.
    """
    if not path_str or not str(path_str).strip():
        raise ValueError("Path string must not be empty.")

    p = Path(path_str).expanduser()
    if not p.is_absolute():
        cand_ws = (WORKSPACE_DIR / p).resolve()
        if cand_ws.exists():
            return cand_ws
        cand_base = (BASE_DIR / p).resolve()
        if cand_base.exists():
            return cand_base
        return cand_ws if WORKSPACE_DIR.exists() else cand_base
    else:
        return p.resolve()

