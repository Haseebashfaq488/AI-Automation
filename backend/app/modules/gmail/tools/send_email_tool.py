from typing import Dict, Any, List
import base64
import mimetypes
import os
from pathlib import Path

from email.message import EmailMessage

from app.core.tool import BaseTool, RiskLevel
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Gmail rejects messages > 35 MB; base64 inflates ~33%, so cap raw attachments
# (plus body) at ~25 MB for a safe margin.
_MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024


def _load_token_path() -> Path | None:
    """Return a path to a ``token.json`` if one exists next to the tool or at
    the project root, otherwise ``None``."""
    p = Path(__file__).resolve().parent / "token.json"
    if p.is_file():
        return p
    root = Path(__file__).resolve().parents[4]
    p2 = root / "token.json"
    if p2.is_file():
        return p2
    return None


def _get_creds() -> Credentials | None:
    token_path = _load_token_path()
    if not token_path:
        return None
    scopes = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly",
    ]
    creds = Credentials.from_authorized_user_file(str(token_path), scopes)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json())
    return creds


class SendEmailTool(BaseTool):
    """Send an email via Gmail API.

    Parameters
    ----------
    to: str
        Recipient email address.
    subject: str (optional)
        Email subject. Omit for a no-subject email.
    body: str
        Email body text.
    attachments: list[str] (optional)
        Absolute paths of local files to attach. Multiple attachments
        supported; total raw size must stay under ~25 MB (Gmail limit).
    """

    name = "send_email"
    description = "Send an email via Gmail API (optional file attachments)."
    risk = RiskLevel.MEDIUM
    input_schema = {
        "type": "object",
        "properties": {
            "to": {"type": "string"},
            "subject": {"type": "string", "default": ""},
            "body": {"type": "string"},
            "attachments": {"type": "array", "items": {"type": "string"}, "default": []},
        },
        "required": ["to", "body"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        to = params["to"]
        subject = params.get("subject") or ""
        body = params["body"]
        attachments: List[str] = params.get("attachments") or []

        # validate + read attachments first (fail fast, before touching Gmail)
        attached_names = []
        total_bytes = len(body.encode())
        parts: List[tuple] = []
        for fp in attachments:
            p = Path(fp)
            if not p.is_file():
                raise RuntimeError(f"Attachment not found: {p}")
            data = p.read_bytes()
            total_bytes += len(data)
            if total_bytes > _MAX_ATTACHMENT_BYTES:
                raise RuntimeError(
                    "Attachments exceed the ~25 MB limit (Gmail rejects messages over 35 MB)."
                )
            mimetype = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
            maintype, _, subtype = mimetype.partition("/")
            parts.append((data, maintype, subtype, p.name))
            attached_names.append(p.name)

        # Mock mode: return simulated success if GMAIL_MOCK env var is set
        if os.getenv("GMAIL_MOCK"):
            return {
                "sent": True,
                "to": to,
                "subject": subject,
                "body": body,
                "attachments": attached_names,
                "mock": True,
            }

        creds = _get_creds()
        if not creds:
            raise RuntimeError(
                "Gmail API credentials not found. "
                "Place a ``token.json`` alongside this tool or at the project root "
                "with Gmail send scope, then re‑run the OAuth flow once."
            )

        try:
            service = build("gmail", "v1", credentials=creds)

            message = EmailMessage()
            message["To"] = to
            message["Subject"] = subject
            message.set_content(body)
            for data, maintype, subtype, filename in parts:
                message.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            service.users().messages().send(userId="me", body={"raw": raw}).execute()

            return {
                "sent": True,
                "to": to,
                "subject": subject,
                "body": body,
                "attachments": attached_names,
            }
        except Exception as exc:
            raise RuntimeError(str(exc))