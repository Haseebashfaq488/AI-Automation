from typing import Dict, Any, List
import base64
import os
from pathlib import Path

from app.core.tool import BaseTool, RiskLevel
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def _load_token_path() -> Path | None:
    """Load Gmail API credentials from token file or return None.

    Looks for ``token.json`` alongside this skill module, then falls back to the
    project ``backend/`` root.  Returns ``None`` if no token is present.
    """
    token_path = Path(__file__).resolve().parent / "token.json"
    if not token_path.exists():
        token_path = Path(__file__).resolve().parents[4] / "token.json"
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(
            str(token_path),
            [
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.readonly",
            ],
        )
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request

            creds.refresh(Request())
            token_path.write_text(creds.to_json())
        return creds
    return None


def _get_creds() -> Credentials | None:
    """Return credentials if present, otherwise respect ``GMAIL_MOCK``."""
    # Mock mode: return a sentinel so the skill returns fake data
    if os.getenv("GMAIL_MOCK"):
        return None  # signal mock below
    return _load_token_path()


class ListRecentEmailsSkill(BaseTool):
    """List recent emails matching a query via Gmail API.

    Parameters
    ----------
    query: str (optional)
        Search query string (e.g. "from:user@example.com subject:hello").
        Defaults to "in:inbox" (recent inbox emails).
    max_results: int (optional)
        Maximum number of emails to return.
    """

    name = "list_recent_emails"
    description = "List recent emails matching a search query."
    risk = RiskLevel.LOW
    category = "skill"
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "default": "in:inbox"},
            "max_results": {"type": "integer", "default": 10},
        },
        "required": [],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query") or "in:inbox"
        max_results = params.get("max_results", 10)

        # Mock mode: return simulated emails
        if os.getenv("GMAIL_MOCK"):
            return {
                "listed": True,
                "query": query,
                "max_results": max_results,
                "emails": [
                    {
                        "id": "msg1",
                        "thread_id": "th1",
                        "subject": "Mock email subject 1",
                        "from": "mock@example.com",
                        "body_preview": "This is a mock email body preview 1",
                        "date": "1700000000",
                    },
                    {
                        "id": "msg2",
                        "thread_id": "th2",
                        "subject": "Mock email subject 2",
                        "from": "mock2@example.com",
                        "body_preview": "This is a mock email body preview 2",
                        "date": "1700000001",
                    },
                ],
            }

        creds = _load_token_path()
        if not creds:
            return {
                "listed": False,
                "query": query,
                "max_results": max_results,
                "emails": [],
                "error": "Gmail API credentials not found. Place a ``token.json`` alongside this skill or at the project root.",
            }

        try:
            service = build("gmail", "v1", credentials=creds)

            results = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
            messages = results.get("messages", [])

            emails: List[Dict[str, Any]] = []
            for msg in messages:
                msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
                payload = msg_data.get("payload", {})
                headers = payload.get("headers", [])

                subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
                sender = next((h["value"] for h in headers if h["name"] == "From"), "")

                snippet = msg_data.get("snippet", "")
                parts = payload.get("parts", [])
                body_text = ""
                if parts:
                    for part in parts:
                        if part.get("mimeType") == "text/plain":
                            data = part.get("body", {}).get("data", "")
                            if data:
                                body_text = base64.urlsafe_b64decode(data).decode(errors="replace")
                            break
                else:
                    body_text = snippet

                emails.append(
                    {
                        "id": msg["id"],
                        "thread_id": msg_data.get("threadId"),
                        "subject": subject,
                        "from": sender,
                        "body_preview": body_text[:200],
                        "date": msg_data.get("internalDate"),
                    }
                )

            return {
                "listed": True,
                "query": query,
                "max_results": max_results,
                "emails": emails,
            }
        except Exception as exc:
            return {
                "listed": False,
                "query": query,
                "max_results": max_results,
                "emails": [],
                "error": str(exc),
            }