from typing import Dict, Any, List

from app.core.tool import BaseTool, RiskLevel
from app.workers.document_worker.word_worker.helpers.paths import resolve_doc_path
from app.workers.document_worker.word_worker.helpers.document import open_docx


class InspectDocxTool(BaseTool):
    """Inspect the structure of a .docx file: headings, paragraph count, tables, styles.

    Parameters
    ----------
    path: str
        Absolute path to the .docx file.
    fs_scope: str (optional)
        Worker scope the path must be inside.
    """

    name = "inspect_docx"
    description = "Inspect a Word document's structure (headings, paragraphs, tables)."
    risk = RiskLevel.LOW
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "fs_scope": {"type": "string"},
        },
        "required": ["path"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_doc_path(params["path"], params.get("fs_scope"))
        doc = open_docx(path)

        headings: List[Dict[str, Any]] = []
        style_counts: Dict[str, int] = {}
        for i, para in enumerate(doc.paragraphs):
            style = para.style.name if para.style else "Normal"
            style_counts[style] = style_counts.get(style, 0) + 1
            if style.startswith("Heading") and para.text.strip():
                headings.append({"index": i, "level": style, "text": para.text.strip()})

        return {
            "path": str(path),
            "paragraph_count": len(doc.paragraphs),
            "table_count": len(doc.tables),
            "section_count": len(doc.sections),
            "headings": headings,
            "heading_count": len(headings),
            "style_counts": style_counts,
        }