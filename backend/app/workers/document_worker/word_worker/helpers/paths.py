from pathlib import Path
from typing import Optional

from app.modules.file_management.helpers.validation import validate_path


def resolve_doc_path(path_str: str, fs_scope: Optional[str] = None) -> Path:
    """Resolve a user/worker‑provided path to an absolute Path.

    - Expands ``~``.
    - If ``fs_scope`` is given, the resolved path must live inside it
      (worker permission boundary).
    - Runs the standard protected‑path validation.
    """
    p = Path(path_str).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    p = p.resolve()

    if fs_scope is not None:
        scope = Path(fs_scope).expanduser().resolve()
        if not p.is_relative_to(scope):
            raise ValueError(f"Path {p} is outside the worker's allowed scope {scope}")

    validate_path(p)
    return p


def ensure_docx_extension(path: Path) -> None:
    """Raise unless the path has a .docx extension."""
    if path.suffix.lower() != ".docx":
        raise ValueError(f"Expected a .docx file, got: {path.name}")


def ensure_docx(path: Path) -> None:
    """Raise unless the path exists and has a .docx extension."""
    if not path.is_file():
        raise FileNotFoundError(f"Document not found: {path}")
    ensure_docx_extension(path)