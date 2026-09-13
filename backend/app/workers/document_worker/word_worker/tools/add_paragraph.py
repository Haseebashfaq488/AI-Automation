from typing import Any, Dict

from app.core.tool import BaseTool, RiskLevel
from app.workers.document_worker.word_worker.helpers.document import open_docx, save_docx
from app.workers.document_worker.word_worker.helpers.paths import resolve_doc_path


class AddParagraphTool(BaseTool):
    """Add a body paragraph to an existing Word document with optional formatting.

    Parameters
    ----------
    path: str
        Absolute path to the .docx file.
    text: str
        Paragraph text content.
    style: str (optional)
        Style name to apply (e.g. 'Normal', 'List Bullet'). Default 'Normal'.
    bold: bool (optional)
        Make the paragraph text bold. Default False.
    italic: bool (optional)
        Make the paragraph text italic. Default False.
    fs_scope: str (optional)
        Worker scope the path must reside within.
    """

    name = "add_paragraph"
    description = "Add a paragraph with optional styling, bold, or italic formatting to a Word document."
    risk = RiskLevel.MEDIUM
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "text": {"type": "string"},
            "style": {"type": "string", "default": "Normal"},
            "bold": {"type": "boolean", "default": False},
            "italic": {"type": "boolean", "default": False},
            "fs_scope": {"type": "string"},
        },
        "required": ["path", "text"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_doc_path(params["path"], params.get("fs_scope"))
        doc = open_docx(path)

        text = str(params["text"])
        style = params.get("style", "Normal")
        bold = bool(params.get("bold", False))
        italic = bool(params.get("italic", False))

        # Check if requested style exists in document styles
        chosen_style = None
        if style and style in doc.styles:
            chosen_style = style

        p = doc.add_paragraph(style=chosen_style)
        run = p.add_run(text)
        if bold:
            run.bold = True
        if italic:
            run.italic = True

        save_docx(doc, path)

        return {
            "path": str(path),
            "added_paragraph_index": len(doc.paragraphs) - 1,
            "paragraph_count": len(doc.paragraphs),
            "style": chosen_style or "default",
            "bold": bold,
            "italic": italic,
        }
