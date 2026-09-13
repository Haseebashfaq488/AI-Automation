from pathlib import Path
from typing import List

# Example protected paths (Windows). Adjust as needed.
PROTECTED_PATHS: List[Path] = [
    Path("C:/Windows"),
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
    Path("C:/System Volume Information"),
]


def is_protected(path: Path) -> bool:
    """Return True if the path is within a protected location."""
    try:
        return any(path.is_relative_to(protected) for protected in PROTECTED_PATHS)
    except Exception:
        # is_relative_to only on Python 3.9+, fallback
        return any(str(path).startswith(str(protected)) for protected in PROTECTED_PATHS)


def validate_path(path: Path) -> None:
    """Validate that a path is safe to operate on.

    Raises ``ValueError`` if the path is protected or otherwise unsafe.
    """
    if is_protected(path):
        raise ValueError(f"Operation not allowed on protected path: {path}")
    # Additional checks can be added here (e.g., length, characters)


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")


def ensure_is_file(path: Path) -> None:
    if not path.is_file():
        raise ValueError(f"Expected a file but got: {path}")


def ensure_is_dir(path: Path) -> None:
    if not path.is_dir():
        raise ValueError(f"Expected a directory but got: {path}")
