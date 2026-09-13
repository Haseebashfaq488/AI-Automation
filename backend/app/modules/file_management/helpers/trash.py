"""Recoverable-delete support: moves items into a backend-local trash folder."""
import shutil
import time
from pathlib import Path

from .paths import BASE_DIR

TRASH_DIR = BASE_DIR / ".jarvis_trash"


def move_to_trash(path: Path) -> Path:
    """Move a file or folder into the trash directory and return its new path.

    The trashed name is prefixed with a millisecond timestamp so repeated
    deletions of same-named items never collide.
    """
    TRASH_DIR.mkdir(parents=True, exist_ok=True)
    dest = TRASH_DIR / f"{int(time.time() * 1000)}_{path.name}"
    shutil.move(str(path), str(dest))
    return dest
