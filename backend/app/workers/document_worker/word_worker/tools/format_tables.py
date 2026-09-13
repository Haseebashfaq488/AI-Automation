from typing import Dict, Any, List

from app.core.tool import BaseTool, RiskLevel
from app.workers.document_worker.word_worker.helpers.paths import resolve_doc_path
from app.workers.document_worker.word_worker.helpers.document import open_docx, save_docx

# Built‑in table styles present in the default python‑docx template
_VALID_STYLES = {"Table Grid", "Light Shading", "Light List", "Medium Shading 1 Accent 1", "Normal Table"}


class FormatTablesTool(BaseTool):
    """Apply a consistent built‑in style to every table in a .docx file.

    Parameters
    ----------
    path: str
        Absolute path to the .docx file.
    style: str (optional)
        Word table style name. Default "Table Grid".
    fs_scope: str (optional)
        Worker scope the path must be inside.
    dry_run: bool (optional)
        Report the affected count without writing.
    """

    name = "format_tables"
    description = "Apply a consistent table style to all tables in a Word document."
    risk = RiskLevel.MEDIUM
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "style": {"type": "string", "default": "Table Grid"},
            "fs_scope": {"type": "string"},
            "dry_run": {"type": "boolean", "default": False},
        },
        "required": ["path"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_doc_path(params["path"], params.get("fs_scope"))
        style = params.get("style", "Table Grid")
        dry = params.get("dry_run", False)
        doc = open_docx(path)

        if style not in _VALID_STYLES:
            # Unknown styles raise from python‑docx — give a helpful message
            try:
                doc.styles[style]
            except KeyError:
                return {
                    "path": str(path),
                    "error": f"Unknown table style '{style}'. Known: {sorted(_VALID_STYLES)}",
                }

        affected = 0
        for table in doc.tables:
            affected += 1
            if not dry:
                table.style = doc.styles[style]

        if affected and not dry:
            save_docx(doc, path)

        return {
            "path": str(path),
            "dry_run": dry,
            "tables_affected": affected,
            "style": style,
        }