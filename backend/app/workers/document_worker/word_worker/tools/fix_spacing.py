from typing import Dict, Any, List

from docx.shared import Pt

from app.core.tool import BaseTool, RiskLevel
from app.workers.document_worker.word_worker.helpers.paths import resolve_doc_path
from app.workers.document_worker.word_worker.helpers.document import open_docx, save_docx


class FixSpacingTool(BaseTool):
    """Normalize paragraph spacing in a .docx file.

    Sets space_before / space_after (in points) for every paragraph, skipping
    empty paragraphs unless include_empty is true.

    Parameters
    ----------
    path: str
        Absolute path to the .docx file.
    space_before: float (optional)
        Points of space before each paragraph. Default 0.
    space_after: float (optional)
        Points of space after each paragraph. Default 8.
    include_empty: bool (optional)
        Also apply to empty paragraphs. Default false.
    fs_scope: str (optional)
        Worker scope the path must be inside.
    dry_run: bool (optional)
        Report the affected count without writing.
    """

    name = "fix_spacing"
    description = "Normalize paragraph spacing (space before/after) in a Word document."
    risk = RiskLevel.MEDIUM
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "space_before": {"type": "number", "default": 0},
            "space_after": {"type": "number", "default": 8},
            "include_empty": {"type": "boolean", "default": False},
            "fs_scope": {"type": "string"},
            "dry_run": {"type": "boolean", "default": False},
        },
        "required": ["path"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_doc_path(params["path"], params.get("fs_scope"))
        before = params.get("space_before", 0)
        after = params.get("space_after", 8)
        include_empty = params.get("include_empty", False)
        dry = params.get("dry_run", False)
        doc = open_docx(path)

        affected = 0
        for para in doc.paragraphs:
            if not include_empty and not para.text.strip():
                continue
            affected += 1
            if not dry:
                para.paragraph_format.space_before = Pt(before)
                para.paragraph_format.space_after = Pt(after)

        if affected and not dry:
            save_docx(doc, path)

        return {
            "path": str(path),
            "dry_run": dry,
            "paragraphs_affected": affected,
            "space_before": before,
            "space_after": after,
        }