from typing import Optional, Dict, Any
import os
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]

# Export MIME types for Google Docs/Sheets/Slides to text/plain or csv
GOOGLE_DOC_EXPORTS = {
    "application/vnd.google-apps.document": "text/plain",
    "application/vnd.google-apps.spreadsheet": "text/csv",
    "application/vnd.google-apps.presentation": "text/plain",
    "application/vnd.google-apps.drawing": "image/png",
}


def get_token_path() -> Optional[Path]:
    """Find drive_token.json or fallback token.json in project paths."""
    candidates = [
        Path(__file__).resolve().parent / "drive_token.json",
        Path(__file__).resolve().parents[4] / "drive_token.json",
        Path(__file__).resolve().parents[4] / "token.json",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def get_drive_creds() -> Optional[Credentials]:
    """Load credentials from token file, refreshing if necessary."""
    token_path = get_token_path()
    if not token_path or not token_path.is_file():
        return None

    try:
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json(), encoding="utf-8")
        return creds
    except Exception:
        # Try without scopes check if token was saved with standard scopes
        try:
            creds = Credentials.from_authorized_user_file(str(token_path))
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                token_path.write_text(creds.to_json(), encoding="utf-8")
            return creds
        except Exception:
            return None


def get_drive_service():
    """Build and return Google Drive v3 client service, or None if unavailable."""
    if os.getenv("DRIVE_MOCK"):
        return None
    creds = get_drive_creds()
    if not creds:
        return None
    try:
        return build("drive", "v3", credentials=creds)
    except Exception:
        return None


def is_mock_mode() -> bool:
    """Return whether mock mode is enabled or credentials are missing in testing."""
    return bool(os.getenv("DRIVE_MOCK"))


def format_file_size(size_bytes: Optional[int]) -> str:
    """Format bytes into human-readable size string."""
    if size_bytes is None:
        return "Unknown"
    try:
        num = float(size_bytes)
    except (ValueError, TypeError):
        return str(size_bytes)

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return f"{num:.1f} {unit}" if unit != "B" else f"{int(num)} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"
