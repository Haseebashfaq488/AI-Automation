import shutil
from pathlib import Path

from docx import Document

from app.workers.document_worker.word_worker.helpers.paths import ensure_docx


def open_docx(path: Path) -> Document:
    """Open a .docx file (raises with a clear message if unreadable)."""
    ensure_docx(path)
    try:
        return Document(str(path))
    except Exception as exc:
        raise ValueError(f"Could not open {path.name}: {exc}")


def backup_docx(path: Path) -> Path:
    """Create ``<name>.backup.docx`` next to the original; returns backup path."""
    ensure_docx(path)
    backup = path.with_name(f"{path.stem}.backup{path.suffix}")
    shutil.copy2(str(path), str(backup))
    return backup


def save_docx(doc: Document, path: Path) -> None:
    """Save the document, verifying it can be re‑opened afterwards."""
    doc.save(str(path))
    # Verify the saved file opens (catches corrupt writes immediately)
    Document(str(path))
