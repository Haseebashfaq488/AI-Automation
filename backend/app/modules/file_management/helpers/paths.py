from pathlib import Path
from typing import Union

# Base directory for the Jarvis backend (project root)
BASE_DIR = Path(__file__).resolve().parents[4]  # backend/app/modules/file_system/helpers/ -> backend


def resolve_path(path_str: str) -> Path:
    """Resolve a user‑provided path string to an absolute Path.

    - Expands ``~`` to the user home directory.
    - Resolves relative paths against the project ``BASE_DIR``.
    - Returns a normalized absolute ``Path``.
    """
    p = Path(path_str).expanduser()
    if not p.is_absolute():
        p = (BASE_DIR / p).resolve()
    else:
        p = p.resolve()
    return p
