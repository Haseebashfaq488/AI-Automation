from typing import Dict, Any, List
import os
from app.core.tool import BaseTool, RiskLevel
from app.modules.drive.helpers.drive_client import (
    get_drive_service,
    is_mock_mode,
    format_file_size,
)


class ListDriveFilesTool(BaseTool):
    """List files and folders from Google Drive.

    Parameters
    ----------
    page_size: int (optional, default 15)
        Number of items to retrieve.
    folder_id: str (optional)
        Specific folder ID to list contents from (e.g. 'root').
    query: str (optional)
        Additional custom Google Drive q search parameter.
    order_by: str (optional, default 'modifiedTime desc')
        Sort order for Drive results.
    """

    name = "list_drive_files"
    description = "List files and folders from Google Drive with metadata, links, and sizes."
    risk = RiskLevel.LOW
    category = "tool"
    input_schema = {
        "type": "object",
        "properties": {
            "page_size": {"type": "integer", "default": 15},
            "folder_id": {"type": "string"},
            "query": {"type": "string"},
            "order_by": {"type": "string", "default": "modifiedTime desc"},
        },
        "required": [],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        page_size = params.get("page_size", 15)
        folder_id = params.get("folder_id")
        user_query = params.get("query")
        order_by = params.get("order_by", "modifiedTime desc")

        # Mock Mode
        if is_mock_mode():
            return {
                "success": True,
                "folder_id": folder_id or "root",
                "total_count": 3,
                "files": [
                    {
                        "id": "mock_drive_file_1",
                        "name": "Project Roadmap 2026.docx",
                        "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "size": 1048576,
                        "size_formatted": "1.0 MB",
                        "modifiedTime": "2026-09-20T10:00:00.000Z",
                        "webViewLink": "https://drive.google.com/file/d/mock_drive_file_1/view",
                        "is_folder": False,
                    },
                    {
                        "id": "mock_drive_file_2",
                        "name": "Budget & Expenses.xlsx",
                        "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "size": 524288,
                        "size_formatted": "512.0 KB",
                        "modifiedTime": "2026-09-21T14:30:00.000Z",
                        "webViewLink": "https://drive.google.com/file/d/mock_drive_file_2/view",
                        "is_folder": False,
                    },
                    {
                        "id": "mock_drive_folder_1",
                        "name": "Automation Backups",
                        "mimeType": "application/vnd.google-apps.folder",
                        "size": None,
                        "size_formatted": "Folder",
                        "modifiedTime": "2026-09-22T08:15:00.000Z",
                        "webViewLink": "https://drive.google.com/drive/folders/mock_drive_folder_1",
                        "is_folder": True,
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
            q_clauses = ["trashed = false"]
            if folder_id:
                q_clauses.append(f"'{folder_id}' in parents")
            if user_query:
                q_clauses.append(user_query)

            q_string = " and ".join(q_clauses)

            results = (
                service.files()
                .list(
                    q=q_string,
                    pageSize=page_size,
                    orderBy=order_by,
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, webViewLink, iconLink)",
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
                "folder_id": folder_id or "root",
                "total_count": len(files),
                "nextPageToken": results.get("nextPageToken"),
                "files": files,
            }

        except Exception as exc:
            return {
                "success": False,
                "error": f"Failed to list Google Drive files: {str(exc)}",
                "files": [],
            }
