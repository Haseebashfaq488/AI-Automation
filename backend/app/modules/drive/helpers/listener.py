import asyncio
import logging
import os
import time
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Set

from app.core.events.bus import get_event_bus
from app.core.events.schema import EventType, JarvisEvent
from app.modules.database.db import SessionLocal
from app.modules.database.repository import Repository
from app.modules.drive.helpers.drive_client import get_drive_service, is_mock_mode, format_file_size

logger = logging.getLogger("jarvis.drive.listener")


class DriveInboundListener:
    """Continuous background listener that monitors Google Drive for recently modified or created files."""

    def __init__(self, poll_interval: float = 300.0):
        self.poll_interval = poll_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._seen_file_versions: Dict[str, str] = {}  # file_id -> modifiedTime
        self._initial_scan_done = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("DriveInboundListener started (poll_interval=%.1fs)", self.poll_interval)

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("DriveInboundListener stopped.")

    async def _poll_loop(self) -> None:
        bus = get_event_bus()

        while self._running:
            try:
                loop = asyncio.get_running_loop()
                files = await loop.run_in_executor(None, self._fetch_recent_files)

                for item in files:
                    file_id = item.get("id")
                    mod_time = item.get("modifiedTime") or ""
                    if not file_id:
                        continue

                    # On initial boot scan, populate the version cache
                    if not self._initial_scan_done:
                        self._seen_file_versions[file_id] = mod_time
                        self._persist_to_db(item)
                        continue

                    last_mod = self._seen_file_versions.get(file_id)
                    if last_mod != mod_time:
                        self._seen_file_versions[file_id] = mod_time
                        file_name = item.get("name", "Untitled")
                        owners = item.get("owners", [])
                        owner_name = owners[0].get("displayName") if owners else "Google Drive"
                        mime_type = item.get("mimeType", "")
                        timestamp_str = time.strftime("%I:%M %p")

                        summary = f"[{timestamp_str}] Drive File: \"{file_name}\" updated by {owner_name}"

                        # 1. Persist to SQLite Hot Feed
                        self._persist_to_db(item, is_unread=True)

                        # 2. Publish to Global Event Bus (SSE Stream)
                        event = JarvisEvent(
                            event_type=EventType.DRIVE_INBOUND_DIGEST,
                            source="drive:listener",
                            title=f"Drive: {file_name}",
                            summary=summary,
                            data={
                                "id": file_id,
                                "name": file_name,
                                "mime_type": mime_type,
                                "owner": owner_name,
                                "modified_time": mod_time,
                                "size": format_file_size(item.get("size")),
                                "time_str": timestamp_str,
                            },
                        )
                        bus.publish(event)
                        logger.info("Emitted Google Drive update event for %s", file_name)

                self._initial_scan_done = True

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.debug("Drive listener poll error (will retry): %s", exc)

            await asyncio.sleep(self.poll_interval)

    def _persist_to_db(self, item: Dict[str, Any], is_unread: bool = False) -> None:
        """Persist drive update to SQLite service_events table."""
        try:
            with SessionLocal() as db:
                repo = Repository(db)
                file_id = item.get("id", "")
                name = item.get("name", "Untitled File")
                owners = item.get("owners", [])
                owner_name = owners[0].get("displayName") if owners else "Drive"
                mime = item.get("mimeType", "")
                snippet = f"File: {name} ({mime}) - Modified: {item.get('modifiedTime', '')}"

                repo.upsert_service_event(
                    event_id=f"drive_{file_id}",
                    service="drive",
                    sender=owner_name,
                    subject_or_title=name,
                    snippet=snippet,
                    full_content=f"Drive File ID: {file_id}\nMIME: {mime}\nLink: {item.get('webViewLink', '')}",
                    is_unread=is_unread,
                )
        except Exception as exc:
            logger.debug("Failed to persist drive event to database: %s", exc)

    def _fetch_recent_files(self) -> List[Dict[str, Any]]:
        """Synchronous fetch executed in worker thread."""
        if is_mock_mode() or os.getenv("TESTING"):
            return [
                {
                    "id": "mock_drive_doc_1",
                    "name": "Project_Roadmap_Q4.docx",
                    "mimeType": "application/vnd.google-apps.document",
                    "modifiedTime": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "owners": [{"displayName": "Haseeb"}],
                    "size": 15420,
                    "webViewLink": "https://drive.google.com/open?id=mock_drive_doc_1",
                }
            ]

        service = get_drive_service()
        if not service:
            return []

        try:
            # Query files ordered by modifiedTime descending
            res = service.files().list(
                pageSize=10,
                orderBy="modifiedTime desc",
                fields="files(id, name, mimeType, modifiedTime, size, owners, webViewLink)",
                q="trashed = false",
            ).execute()
            return res.get("files", [])
        except Exception as exc:
            logger.debug("Error fetching Drive files via API: %s", exc)
            return []


# Global singleton instance
_drive_listener: Optional[DriveInboundListener] = None


def get_drive_listener() -> DriveInboundListener:
    global _drive_listener
    if _drive_listener is None:
        _drive_listener = DriveInboundListener()
    return _drive_listener
