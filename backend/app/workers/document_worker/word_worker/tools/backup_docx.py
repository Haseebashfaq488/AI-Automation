from typing import Dict, Any

from app.core.tool import BaseTool, RiskLevel
from app.workers.document_worker.word_worker.helpers.paths import resolve_doc_path
from app.workers.document_worker.word_worker.helpers.document import backup_docx


class BackupDocxTool(BaseTool):
    """Create a backup copy of a .docx file before modifying it.

    Creates ``<name>.backup.docx`` next to the original.

    Parameters
    ----------
    path: str
        Absolute path to the .docx file.
    fs_scope: str (optional)
        Worker scope the path must be inside.
    """

    name = "backup_docx"
    description = "Create a .backup.docx copy of a Word document before editing."
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
        backup = backup_docx(path)
        return {"path": str(path), "backup": str(backup)}