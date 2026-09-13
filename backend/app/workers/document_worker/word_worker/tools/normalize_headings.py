from typing import Dict, Any, List

from app.core.tool import BaseTool, RiskLevel
from app.workers.document_worker.word_worker.helpers.paths import resolve_doc_path
from app.workers.document_worker.word_worker.helpers.document import open_docx, save_docx

# Map common "looks like a heading" patterns to Word heading styles
_PREFIX_LEVELS = [
    ("# ", 1), ("## ", 2), ("### ", 3), ("#### ", 4), ("##### ", 5),
]


class NormalizeHeadingsTool(BaseTool):
    """Normalize heading styles in a .docx file.

    Two modes:
    - explicit: paragraphs whose style already starts with "Heading" are kept;
      markdown‑style prefixes (#, ##, ###) in the text are converted to real
      Heading 1‑3 styles (prefix text removed).
    - infer: short bold‑ish lines are left untouched (Word does not expose
      bold reliably per‑run here) — use explicit mode.

    Parameters
    ----------
    path: str
        Absolute path to the .docx file.
    fs_scope: str (optional)
        Worker scope the path must be inside.
    dry_run: bool (optional)
        Report what would change without writing.
    """

    name = "normalize_headings"
    description = "Convert markdown-style # headings into real Word heading styles."
    risk = RiskLevel.MEDIUM
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "fs_scope": {"type": "string"},
            "dry_run": {"type": "boolean", "default": False},
        },
        "required": ["path"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_doc_path(params["path"], params.get("fs_scope"))
        dry = params.get("dry_run", False)
        doc = open_docx(path)

        changes: List[Dict[str, Any]] = []
        for i, para in enumerate(doc.paragraphs):
            text = para.text
            for prefix, level in _PREFIX_LEVELS:
                if text.startswith(prefix) and len(text) > len(prefix):
                    new_text = text[len(prefix):].strip()
                    changes.append(
                        {"index": i, "from": text, "to": new_text, "heading_level": level}
                    )
                    if not dry:
                        para.text = new_text
                        para.style = doc.styles[f"Heading {level}"]
                    break

        if changes and not dry:
            save_docx(doc, path)

        return {
            "path": str(path),
            "dry_run": dry,
            "changes": len(changes),
            "details": changes,
        }