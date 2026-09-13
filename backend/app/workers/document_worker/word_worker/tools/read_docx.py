from typing import Dict, Any, List

from app.core.tool import BaseTool, RiskLevel
from app.workers.document_worker.word_worker.helpers.paths import resolve_doc_path
from app.workers.document_worker.word_worker.helpers.document import open_docx


class ReadDocxTool(BaseTool):
    """Read the text content of a .docx file, with optional paragraph range.

    Parameters
    ----------
    path: str
        Absolute path to the .docx file.
    start: int (optional)
        First paragraph index (0‑based). Default 0.
    limit: int (optional)
        Max paragraphs to return. Default 200.
    fs_scope: str (optional)
        Worker scope the path must be inside.
    """

    name = "read_docx"
    description = "Read text content from a Word document."
    risk = RiskLevel.LOW
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "start": {"type": "integer", "default": 0},
            "limit": {"type": "integer", "default": 200},
            "fs_scope": {"type": "string"},
        },
        "required": ["path"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_doc_path(params["path"], params.get("fs_scope"))
        start = params.get("start", 0)
        limit = params.get("limit", 200)
        doc = open_docx(path)

        paragraphs: List[Dict[str, Any]] = []
        total = len(doc.paragraphs)
        for i in range(start, min(start + limit, total)):
            para = doc.paragraphs[i]
            paragraphs.append(
                {
                    "index": i,
                    "style": para.style.name if para.style else "Normal",
                    "text": para.text,
                }
            )

        return {
            "path": str(path),
            "total_paragraphs": total,
            "returned": len(paragraphs),
            "paragraphs": paragraphs,
        }