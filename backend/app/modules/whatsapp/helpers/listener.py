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

                chats = await client.list_chats(limit=15)
                for chat in chats:
                    chat_id = chat.get("id") or chat.get("name")
                    if not chat_id:
                        continue

                    preview = chat.get("preview") or ""
                    unread_count = chat.get("unread") or 0
                    last_seen = self._seen_previews.get(chat_id)

                    # If this is the initial scan on startup, populate cache without blasting old events
                    if not self._initial_scan_done:
                        self._seen_previews[chat_id] = preview
                        continue

                    # If the preview has changed or there are unread messages not yet seen
                    if preview and preview != last_seen and (unread_count > 0 or last_seen is not None):
                        self._seen_previews[chat_id] = preview
                        chat_name = chat.get("name") or chat_id
                        timestamp_str = time.strftime("%I:%M %p")

                        # Summarize content
                        summary = f"[{timestamp_str}] {chat_name}: {preview}"
                        if unread_count > 1:
                            summary += f" ({unread_count} unread)"

                        # 1. Persist into SQLite Hot Activity Feed
                        self._persist_to_db(chat_id, chat_name, preview, unread_count, is_group=chat.get("isGroup", False))

                        # 2. Publish to Global Event Bus (SSE)
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
                                "is_group": chat.get("isGroup", False),
                                "time_str": timestamp_str,
                            },
                        )
                        bus.publish(event)
                        logger.info("Emitted WhatsApp inbound digest event for %s", chat_name)

                self._initial_scan_done = True

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.debug("WhatsApp listener poll error (will retry): %s", exc)

            await asyncio.sleep(self.poll_interval)

    def _persist_to_db(self, chat_id: str, chat_name: str, preview: str, unread_count: int, is_group: bool = False) -> None:
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
                    full_content=f"Chat: {chat_name}\nLatest preview: {preview}\nUnread count: {unread_count}",
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
