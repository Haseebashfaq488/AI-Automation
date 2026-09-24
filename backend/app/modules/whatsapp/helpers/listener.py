import asyncio
import logging
import time
from typing import Dict, Optional, Set

from app.core.events.bus import get_event_bus
from app.core.events.schema import EventType, JarvisEvent
from app.modules.whatsapp.helpers.client import get_client

logger = logging.getLogger("jarvis.whatsapp.listener")


class WhatsAppInboundListener:
    """Continuous background listener that monitors WhatsApp chats and emits digest events."""

    def __init__(self, poll_interval: float = 8.0):
        self.poll_interval = poll_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        # Cache to track latest seen message preview per chat to avoid duplicate alerts
        self._seen_previews: Dict[str, str] = {}
        self._initial_scan_done = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("WhatsAppInboundListener started (poll_interval=%.1fs)", self.poll_interval)

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("WhatsAppInboundListener stopped.")

    async def sync_recent_chats(self, limit: int = 25) -> int:
        """Fetch and persist recent WhatsApp chats into SQLite service_events immediately."""
        client = get_client()
        try:
            status_res = await client.status()
            if status_res.get("state") != "ready":
                return 0

            chats = await client.list_chats(limit=limit)
            persisted_count = 0
            for chat in chats:
                chat_id = chat.get("id") or chat.get("name")
                if not chat_id:
                    continue

                chat_name = chat.get("name") or chat_id
                preview = chat.get("preview") or ""
                unread_count = chat.get("unread") or 0
                is_group = chat.get("isGroup", False)
                timestamp = chat.get("timestamp") or time.strftime("%I:%M %p")

                self._persist_to_db(
                    chat_id=chat_id,
                    chat_name=chat_name,
                    preview=preview,
                    unread_count=unread_count,
                    is_group=is_group,
                    timestamp_str=timestamp,
                )
                self._seen_previews[chat_id] = preview
                persisted_count += 1

            return persisted_count
        except Exception as exc:
            logger.debug("Error during WhatsApp sync_recent_chats: %s", exc)
            return 0

    async def _poll_loop(self) -> None:
        client = get_client()
        bus = get_event_bus()

        while self._running:
            try:
                # Check status first
                status_res = await client.status()
                if status_res.get("state") != "ready":
                    await asyncio.sleep(self.poll_interval)
                    continue

                chats = await client.list_chats(limit=20)
                for chat in chats:
                    chat_id = chat.get("id") or chat.get("name")
                    if not chat_id:
                        continue

                    chat_name = chat.get("name") or chat_id
                    preview = chat.get("preview") or ""
                    unread_count = chat.get("unread") or 0
                    is_group = chat.get("isGroup", False)
                    timestamp_str = chat.get("timestamp") or time.strftime("%I:%M %p")
                    last_seen = self._seen_previews.get(chat_id)

                    # Always persist to DB so 24h feed & 7-day memory are up to date
                    self._persist_to_db(
                        chat_id=chat_id,
                        chat_name=chat_name,
                        preview=preview,
                        unread_count=unread_count,
                        is_group=is_group,
                        timestamp_str=timestamp_str,
                    )

                    # If preview changed or new unread messages arrived after startup, emit event to frontend SSE
                    if self._initial_scan_done and ((preview and preview != last_seen) or unread_count > 0):
                        self._seen_previews[chat_id] = preview
                        summary = f"[{timestamp_str}] {chat_name}: {preview}"
                        if unread_count > 1:
                            summary += f" ({unread_count} unread)"

                        # Publish to Global Event Bus (SSE)
                        event = JarvisEvent(
                            event_type=EventType.WHATSAPP_INBOUND_DIGEST,
                            source="whatsapp:listener",
                            title=f"WhatsApp: {chat_name}",
                            summary=summary,
                            data={
                                "chat_id": chat_id,
                                "name": chat_name,
                                "preview": preview,
                                "unread": unread_count,
                                "is_group": is_group,
                                "time_str": timestamp_str,
                            },
                        )
                        bus.publish(event)
                        logger.info("Emitted WhatsApp inbound digest event for %s", chat_name)
                    else:
                        self._seen_previews[chat_id] = preview

                self._initial_scan_done = True

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.debug("WhatsApp listener poll error (will retry): %s", exc)

            await asyncio.sleep(self.poll_interval)

    def _persist_to_db(
        self,
        chat_id: str,
        chat_name: str,
        preview: str,
        unread_count: int,
        is_group: bool = False,
        timestamp_str: Optional[str] = None,
    ) -> None:
        """Persist incoming chat preview to SQLite service_events table."""
        try:
            from app.modules.database.db import SessionLocal
            from app.modules.database.repository import Repository
            with SessionLocal() as db:
                repo = Repository(db)
                repo.upsert_service_event(
                    event_id=f"wa_{chat_id}",
                    service="whatsapp",
                    sender=chat_name,
                    subject_or_title=f"Chat: {chat_name}" + (" (Group)" if is_group else ""),
                    snippet=preview,
                    full_content=f"Chat: {chat_name}\nLatest preview: {preview}\nUnread count: {unread_count}\nTimestamp: {timestamp_str or 'Recent'}",
                    is_unread=unread_count > 0,
                )
        except Exception as exc:
            logger.debug("Failed to persist WhatsApp event to database: %s", exc)



# Global singleton instance
_whatsapp_listener: Optional[WhatsAppInboundListener] = None


def get_whatsapp_listener() -> WhatsAppInboundListener:
    global _whatsapp_listener
    if _whatsapp_listener is None:
        _whatsapp_listener = WhatsAppInboundListener()
    return _whatsapp_listener
