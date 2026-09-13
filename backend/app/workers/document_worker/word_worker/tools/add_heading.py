from typing import Any, Dict

from app.core.tool import BaseTool, RiskLevel
from app.workers.document_worker.word_worker.helpers.document import open_docx, save_docx
from app.workers.document_worker.word_worker.helpers.paths import resolve_doc_path


class AddHeadingTool(BaseTool):
    """Add a structured heading to an existing Word document.

    Parameters
    ----------
    path: str
        Absolute path to the .docx file.
    text: str
        Heading text.
    level: int (optional)
        Heading level from 1 to 9 (default: 1).
    fs_scope: str (optional)
        Worker scope the path must reside within.
    """

    name = "add_heading"
    description = "Add a heading (level 1-9) to an existing Word document."
    risk = RiskLevel.MEDIUM
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "text": {"type": "string"},
            "level": {"type": "integer", "default": 1, "minimum": 1, "maximum": 9},
            "fs_scope": {"type": "string"},
        },
        "required": ["path", "text"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_doc_path(params["path"], params.get("fs_scope"))
        doc = open_docx(path)

        text = str(params["text"]).strip()
        level = int(params.get("level", 1))
        # Ensure level is within 1 to 9
        clamped_level = max(1, min(level, 9))

        doc.add_heading(text, level=clamped_level)
        save_docx(doc, path)

        return {
            "path": str(path),
            "added_heading": text,
            "level": clamped_level,
            "paragraph_count": len(doc.paragraphs),
        }
