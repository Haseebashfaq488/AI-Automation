from typing import Dict, Any
import os
import mimetypes
from pathlib import Path
from app.core.tool import BaseTool, RiskLevel
from app.modules.drive.helpers.drive_client import (
    get_drive_service,
    is_mock_mode,
    format_file_size,
)
from googleapiclient.http import MediaFileUpload


class UploadDriveFileTool(BaseTool):
    """Upload a local file to Google Drive.

    Parameters
    ----------
    path: str (required)
        Absolute path to the local file to upload.
    folder_id: str (optional)
        Drive folder ID to place the uploaded file into.
    name: str (optional)
        Name for the file in Google Drive (defaults to local file name).
    """

    name = "upload_drive_file"
    description = "Upload a local file to Google Drive."
    risk = RiskLevel.MEDIUM
    category = "tool"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "folder_id": {"type": "string"},
            "name": {"type": "string"},
        },
        "required": ["path"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        file_path_str = params.get("path") or params.get("file_path")
        folder_id = params.get("folder_id")
        target_name = params.get("name") or params.get("file_name")

        if not file_path_str:
            return {"success": False, "error": "path parameter is required"}

        local_path = Path(file_path_str).resolve()
        if not local_path.is_file():
            return {"success": False, "error": f"Local file not found: {file_path_str}"}

        upload_name = target_name or local_path.name
        file_size = local_path.stat().st_size

        # Mock Mode
        if is_mock_mode():
            return {
                "success": True,
                "file_id": "mock_uploaded_drive_file_id",
                "name": upload_name,
                "folder_id": folder_id or "root",
                "size": file_size,
                "size_formatted": format_file_size(file_size),
                "webViewLink": "https://drive.google.com/file/d/mock_uploaded_drive_file_id/view",
            }

        service = get_drive_service()
        if not service:
            return {
                "success": False,
                "error": "Google Drive credentials not found or unauthenticated. Run setup_drive_oauth.py to authorize.",
            }

        try:
            mime_type, _ = mimetypes.guess_type(str(local_path))
            mime_type = mime_type or "application/octet-stream"

            file_metadata = {"name": upload_name}
            if folder_id:
                file_metadata["parents"] = [folder_id]

            media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=True)

            file = (
                service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, name, mimeType, size, webViewLink",
                )
                .execute()
            )

            return {
                "success": True,
                "file_id": file.get("id"),
                "name": file.get("name"),
                "mimeType": file.get("mimeType"),
                "folder_id": folder_id or "root",
                "size": file_size,
                "size_formatted": format_file_size(file_size),
                "webViewLink": file.get("webViewLink"),
            }

        except Exception as exc:
            return {
                "success": False,
                "error": f"Failed to upload '{file_path_str}' to Google Drive: {str(exc)}",
            }
