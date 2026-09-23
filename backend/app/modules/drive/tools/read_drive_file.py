from typing import Dict, Any
import io
import os
from pathlib import Path
from app.core.tool import BaseTool, RiskLevel
from app.modules.drive.helpers.drive_client import (
    get_drive_service,
    is_mock_mode,
    format_file_size,
    GOOGLE_DOC_EXPORTS,
)
from googleapiclient.http import MediaIoBaseDownload


class ReadDriveFileTool(BaseTool):
    """Read the content or download a Google Drive file by ID.

    Parameters
    ----------
    file_id: str (required)
        The Google Drive file ID.
    destination: str (optional)
        Local file path to save the downloaded file to.
    max_bytes: int (optional, default 1048576)
        Max characters/bytes of text content to return in the response.
    """

    name = "read_drive_file"
    description = "Read text content or download a file from Google Drive by file ID."
    risk = RiskLevel.LOW
    category = "tool"
    input_schema = {
        "type": "object",
        "properties": {
            "file_id": {"type": "string"},
            "destination": {"type": "string"},
            "max_bytes": {"type": "integer", "default": 1048576},
        },
        "required": ["file_id"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        file_id = params.get("file_id")
        destination = params.get("destination")
        max_bytes = params.get("max_bytes", 1048576)

        if not file_id:
            return {"success": False, "error": "file_id is required"}

        # Mock Mode
        if is_mock_mode():
            mock_content = (
                "Jarvis Project Roadmap 2026\n"
                "1. WhatsApp automation & sidecar optimization\n"
                "2. Google Drive & Gmail unified productivity module\n"
                "3. Autonomous background worker engine\n"
            )
            if destination:
                dest_path = Path(destination)
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                dest_path.write_text(mock_content, encoding="utf-8")
                return {
                    "success": True,
                    "file_id": file_id,
                    "name": "Project Roadmap 2026.docx",
                    "saved_to": str(dest_path.resolve()),
                    "size": len(mock_content),
                    "size_formatted": format_file_size(len(mock_content)),
                }
            return {
                "success": True,
                "file_id": file_id,
                "name": "Project Roadmap 2026.docx",
                "mimeType": "text/plain",
                "content": mock_content,
                "size": len(mock_content),
                "size_formatted": format_file_size(len(mock_content)),
            }

        service = get_drive_service()
        if not service:
            return {
                "success": False,
                "error": "Google Drive credentials not found or unauthenticated. Run setup_drive_oauth.py to authorize.",
            }

        try:
            # 1. Fetch file metadata
            metadata = (
                service.files()
                .get(fileId=file_id, fields="id, name, mimeType, size, webViewLink")
                .execute()
            )
            file_name = metadata.get("name", "downloaded_file")
            mime_type = metadata.get("mimeType", "")

            # 2. Determine if export or direct download is needed
            fh = io.BytesIO()
            if mime_type in GOOGLE_DOC_EXPORTS:
                export_mime = GOOGLE_DOC_EXPORTS[mime_type]
                request = service.files().export_media(fileId=file_id, mimeType=export_mime)
            else:
                request = service.files().get_media(fileId=file_id)

            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

            raw_bytes = fh.getvalue()

            # 3. Handle optional destination save
            if destination:
                dest_path = Path(destination)
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                dest_path.write_bytes(raw_bytes)
                return {
                    "success": True,
                    "file_id": file_id,
                    "name": file_name,
                    "mimeType": mime_type,
                    "saved_to": str(dest_path.resolve()),
                    "size": len(raw_bytes),
                    "size_formatted": format_file_size(len(raw_bytes)),
                    "webViewLink": metadata.get("webViewLink"),
                }

            # 4. Attempt to decode as text
            try:
                text_content = raw_bytes[:max_bytes].decode("utf-8")
                is_truncated = len(raw_bytes) > max_bytes
                return {
                    "success": True,
                    "file_id": file_id,
                    "name": file_name,
                    "mimeType": mime_type,
                    "content": text_content,
                    "is_truncated": is_truncated,
                    "size": len(raw_bytes),
                    "size_formatted": format_file_size(len(raw_bytes)),
                    "webViewLink": metadata.get("webViewLink"),
                }
            except UnicodeDecodeError:
                return {
                    "success": True,
                    "file_id": file_id,
                    "name": file_name,
                    "mimeType": mime_type,
                    "is_binary": True,
                    "message": f"Binary file ({format_file_size(len(raw_bytes))}). Provide 'destination' parameter to save locally.",
                    "size": len(raw_bytes),
                    "size_formatted": format_file_size(len(raw_bytes)),
                    "webViewLink": metadata.get("webViewLink"),
                }

        except Exception as exc:
            return {
                "success": False,
                "error": f"Failed to read Drive file '{file_id}': {str(exc)}",
            }
