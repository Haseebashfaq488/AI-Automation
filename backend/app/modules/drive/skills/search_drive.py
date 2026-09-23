from typing import Dict, Any, List
import os
from app.core.tool import BaseTool, RiskLevel
from app.modules.drive.helpers.drive_client import (
    get_drive_service,
    is_mock_mode,
    format_file_size,
)

TYPE_MIME_MAP = {
    "document": "application/vnd.google-apps.document",
    "spreadsheet": "application/vnd.google-apps.spreadsheet",
    "presentation": "application/vnd.google-apps.presentation",
    "folder": "application/vnd.google-apps.folder",
    "pdf": "application/pdf",
    "image": "image/",
    "audio": "audio/",
    "video": "video/",
}


class SearchDriveSkill(BaseTool):
    """Search Google Drive files by keyword, full-text content, and file type.

    Parameters
    ----------
    query: str (required)
        Search keywords or phrases.
    file_type: str (optional)
        Filter by type ('document', 'spreadsheet', 'presentation', 'pdf', 'image', 'folder').
    max_results: int (optional, default 10)
        Maximum number of matching files to return.
    """

    name = "search_drive"
    description = "Search Google Drive files by name, content, and type."
    risk = RiskLevel.LOW
    category = "skill"
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "file_type": {"type": "string"},
            "max_results": {"type": "integer", "default": 10},
        },
        "required": ["query"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "").strip()
        file_type = params.get("file_type")
        max_results = params.get("max_results", 10)

        if not query:
            return {"success": False, "error": "query parameter is required"}

        # Mock Mode
        if is_mock_mode():
            return {
                "success": True,
                "query": query,
                "file_type": file_type,
                "total_count": 2,
                "files": [
                    {
                        "id": "mock_search_file_1",
                        "name": f"{query} Overview.docx",
                        "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "size": 1048576,
                        "size_formatted": "1.0 MB",
                        "modifiedTime": "2026-09-20T12:00:00.000Z",
                        "webViewLink": "https://drive.google.com/file/d/mock_search_file_1/view",
                        "is_folder": False,
                    },
                    {
                        "id": "mock_search_file_2",
                        "name": f"{query} Notes.txt",
                        "mimeType": "text/plain",
                        "size": 12288,
                        "size_formatted": "12.0 KB",
                        "modifiedTime": "2026-09-21T09:00:00.000Z",
                        "webViewLink": "https://drive.google.com/file/d/mock_search_file_2/view",
                        "is_folder": False,
                    },
                ],
            }

        service = get_drive_service()
        if not service:
            return {
                "success": False,
                "error": "Google Drive credentials not found or unauthenticated. Run setup_drive_oauth.py to authorize.",
                "files": [],
            }

        try:
            # Escape query single quotes
            escaped_q = query.replace("'", "\\'")
            clauses = [
                "trashed = false",
                f"(name contains '{escaped_q}' or fullText contains '{escaped_q}')",
            ]

            if file_type and file_type.lower() in TYPE_MIME_MAP:
                mime_prefix = TYPE_MIME_MAP[file_type.lower()]
                if mime_prefix.endswith("/"):
                    clauses.append(f"mimeType contains '{mime_prefix}'")
                else:
                    clauses.append(f"mimeType = '{mime_prefix}'")

            q_string = " and ".join(clauses)

            results = (
                service.files()
                .list(
                    q=q_string,
                    pageSize=max_results,
                    orderBy="modifiedTime desc",
                    fields="files(id, name, mimeType, size, modifiedTime, webViewLink, iconLink)",
                )
                .execute()
            )

            raw_files = results.get("files", [])
            files = []
            for f in raw_files:
                is_folder = f.get("mimeType") == "application/vnd.google-apps.folder"
                raw_size = int(f["size"]) if f.get("size") is not None else None
                files.append(
                    {
                        "id": f.get("id"),
                        "name": f.get("name"),
                        "mimeType": f.get("mimeType"),
                        "size": raw_size,
                        "size_formatted": "Folder" if is_folder else format_file_size(raw_size),
                        "modifiedTime": f.get("modifiedTime"),
                        "webViewLink": f.get("webViewLink"),
                        "is_folder": is_folder,
                    }
                )

            return {
                "success": True,
                "query": query,
                "file_type": file_type,
                "total_count": len(files),
                "files": files,
            }

        except Exception as exc:
            return {
                "success": False,
                "error": f"Search failed for query '{query}': {str(exc)}",
                "files": [],
            }
