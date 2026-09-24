import asyncio
import html
import logging
import os
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from app.core.events.bus import get_event_bus
from app.core.events.schema import EventType, JarvisEvent

logger = logging.getLogger("jarvis.gmail.listener")


def _load_creds():
    """Load Google OAuth credentials with multiple fallback search paths."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        candidates = [
            Path(__file__).resolve().parent / "token.json",
            Path(__file__).resolve().parents[3] / "token.json",
            Path(__file__).resolve().parents[4] / "token.json",
            Path("token.json").resolve(),
            Path("backend/token.json").resolve(),
        ]
        token_path = None
        for p in candidates:
            if p.is_file():
                token_path = p
                break

        if token_path and token_path.exists():
            creds = Credentials.from_authorized_user_file(
                str(token_path),
                [
                    "https://www.googleapis.com/auth/gmail.send",
                    "https://www.googleapis.com/auth/gmail.readonly",
                ],
            )
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                token_path.write_text(creds.to_json(), encoding="utf-8")
            return creds
    except Exception as exc:
        logger.debug("Could not load Gmail credentials: %s", exc)
    return None


class GmailInboundListener:
    """Continuous background listener that monitors Gmail for new unread messages and 24h updates."""

    def __init__(self, poll_interval: float = 300.0):
        self.poll_interval = poll_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._seen_ids: Set[str] = set()
        self._initial_scan_done = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("GmailInboundListener started (poll_interval=%.1fs)", self.poll_interval)

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("GmailInboundListener stopped.")

    async def _poll_loop(self) -> None:
        bus = get_event_bus()

        while self._running:
            try:
                creds = _load_creds()
                if not creds and not os.getenv("GMAIL_MOCK"):
                    # Credentials not available yet, sleep and wait
                    await asyncio.sleep(self.poll_interval)
                    continue

                loop = asyncio.get_running_loop()
                emails = await loop.run_in_executor(None, lambda: self._fetch_recent_emails(creds))

                for email_item in emails:
                    msg_id = email_item.get("id")
                    if not msg_id:
                        continue

                    is_unread = email_item.get("is_unread", False)
                    event_ts = email_item.get("timestamp")

                    if not self._initial_scan_done:
                        self._seen_ids.add(msg_id)
                        self._persist_to_db(email_item, is_unread=is_unread, event_timestamp=event_ts)
                        continue

                    if msg_id not in self._seen_ids:
                        self._seen_ids.add(msg_id)
                        sender = email_item.get("from", "Unknown Sender")
                        subject = email_item.get("subject", "(No Subject)")
                        snippet = email_item.get("snippet", "")
                        timestamp_str = time.strftime("%I:%M %p")

                        summary = f"[{timestamp_str}] From {sender}: \"{subject}\""
                        if snippet:
                            summary += f" — {snippet[:80]}..."

                        # 1. Persist to SQLite Hot Activity Feed
                        self._persist_to_db(email_item, is_unread=is_unread, event_timestamp=event_ts)

                        # 2. Publish to Global Event Bus (SSE)
                        event = JarvisEvent(
                            event_type=EventType.GMAIL_INBOUND_DIGEST,
                            source="gmail:listener",
                            title=f"Email: {subject[:50]}",
                            summary=summary,
                            data={
                                "id": msg_id,
                                "sender": sender,
                                "subject": subject,
                                "snippet": snippet,
                                "date": email_item.get("date", ""),
                                "time_str": timestamp_str,
                            },
                        )
                        bus.publish(event)
                        logger.info("Emitted Gmail inbound digest event for email from %s", sender)

                self._initial_scan_done = True

                # Trigger memory daily digest refresh in background thread
                try:
                    from app.modules.memory.service_memory import get_service_memory_manager
                    loop.run_in_executor(None, get_service_memory_manager().aggregate_daily_digest)
                except Exception:
                    pass


            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.debug("Gmail listener poll error (will retry): %s", exc)

            await asyncio.sleep(self.poll_interval)

    def _persist_to_db(
        self,
        email_item: Dict[str, Any],
        is_unread: bool = False,
        event_timestamp: Optional[datetime] = None,
    ) -> None:
        """Persist email to SQLite service_events table."""
        try:
            from app.modules.database.db import SessionLocal
            from app.modules.database.repository import Repository
            with SessionLocal() as db:
                repo = Repository(db)
                msg_id = email_item.get("id", "")
                sender = email_item.get("from", "Unknown")
                subject = email_item.get("subject", "(No Subject)")
                snippet = email_item.get("snippet", "")

                repo.upsert_service_event(
                    event_id=f"gmail_{msg_id}",
                    service="gmail",
                    sender=sender,
                    subject_or_title=subject,
                    snippet=snippet,
                    full_content=f"From: {sender}\nSubject: {subject}\nDate: {email_item.get('date', '')}\nSnippet: {snippet}",
                    is_unread=is_unread,
                    event_timestamp=event_timestamp,
                )
        except Exception as exc:
            logger.debug("Failed to persist Gmail event to database: %s", exc)

    def _fetch_recent_emails(self, creds) -> List[Dict[str, Any]]:
        """Synchronous fetch executed in worker thread."""
        if not creds:
            if os.getenv("GMAIL_MOCK"):
                return [
                    {
                        "id": "mock_msg_1",
                        "from": "alice@example.com",
                        "subject": "Mock Project Update",
                        "snippet": "Here is the latest status on the automation task...",
                        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "is_unread": True,
                        "timestamp": datetime.now(UTC),
                    }
                ]
            return []

        try:
            from googleapiclient.discovery import build

            service = build("gmail", "v1", credentials=creds, cache_discovery=False)
            # Query last 24h emails (or fallback to recent 20 inbox)
            res = service.users().messages().list(userId="me", q="newer_than:2d", maxResults=20).execute()
            messages = res.get("messages", [])
            if not messages:
                res = service.users().messages().list(userId="me", q="in:inbox", maxResults=15).execute()
                messages = res.get("messages", [])

            results = []
            for msg_meta in messages:
                m_id = msg_meta["id"]
                msg_data = service.users().messages().get(
                    userId="me", id=m_id, format="metadata",
                    metadataHeaders=["From", "Subject", "Date"]
                ).execute()

                headers = {
                    h["name"].lower(): h["value"]
                    for h in msg_data.get("payload", {}).get("headers", [])
                }
                label_ids = msg_data.get("labelIds", [])
                is_unread = "UNREAD" in label_ids

                snippet = html.unescape(msg_data.get("snippet", ""))
                subject = html.unescape(headers.get("subject", "(No Subject)"))
                sender = headers.get("from", "Unknown")

                # Parse timestamp from internalDate (milliseconds)
                event_ts = None
                internal_date = msg_data.get("internalDate")
                if internal_date:
                    try:
                        event_ts = datetime.fromtimestamp(int(internal_date) / 1000.0, tz=UTC)
                    except Exception:
                        event_ts = None

                results.append({
                    "id": m_id,
                    "from": sender,
                    "subject": subject,
                    "snippet": snippet,
                    "date": headers.get("date", ""),
                    "is_unread": is_unread,
                    "timestamp": event_ts or datetime.now(UTC),
                })
            return results
        except Exception as exc:
            logger.debug("Error fetching Gmail messages via API: %s", exc)
            return []


# Global singleton instance
_gmail_listener: Optional[GmailInboundListener] = None


def get_gmail_listener() -> GmailInboundListener:
    global _gmail_listener
    if _gmail_listener is None:
        _gmail_listener = GmailInboundListener()
    return _gmail_listener
