"""7-Day Temporal Multi-Service Memory & 24-Hour Hot Activity Feed Manager.

This module unifies ambient data across WhatsApp, Gmail, and Google Drive:
1. Formats ambient memory snapshots to inject into Jarvis's brain prompt.
2. Builds rolling daily digests (7-day window) from raw service events.
3. Automatically prunes records older than the 7-day retention horizon.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, UTC, timedelta
from typing import Any, Dict, List, Optional

from app.modules.database.db import SessionLocal
from app.modules.database.repository import Repository
from app.modules.database.models import ServiceEvent, ServiceDailyDigest

logger = logging.getLogger("jarvis.memory.service")


class ServiceMemoryManager:
    """Manages ambient multi-service memory across WhatsApp, Gmail, and Google Drive."""

    def __init__(self, retention_days: int = 7, hot_window_hours: int = 24):
        self.retention_days = retention_days
        self.hot_window_hours = hot_window_hours

    def get_hot_events(
        self,
        service: Optional[str] = None,
        hours: Optional[int] = None,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve recent activity events within the hot window (e.g., 24h)."""
        h = hours or self.hot_window_hours
        with SessionLocal() as db:
            repo = Repository(db)
            events = repo.list_service_events(service=service, hours=h, unread_only=unread_only, limit=limit)
            return [
                {
                    "id": evt.id,
                    "service": evt.service,
                    "sender": evt.sender,
                    "title": evt.subject_or_title,
                    "snippet": evt.snippet,
                    "full_content": evt.full_content,
                    "is_unread": bool(evt.is_unread),
                    "timestamp": evt.event_timestamp.isoformat() if evt.event_timestamp else None,
                }
                for evt in events
            ]

    def get_unread_summary(self) -> Dict[str, Any]:
        """Return unread counts per service within the hot window."""
        with SessionLocal() as db:
            repo = Repository(db)
            return repo.get_service_unread_counts(hours=self.hot_window_hours)

    def get_7day_digests(self, days: Optional[int] = None, service: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve structured daily digests for the past N days (default 7)."""
        d = days or self.retention_days
        with SessionLocal() as db:
            repo = Repository(db)
            digests = repo.list_daily_digests(days=d, service=service)
            results = []
            for item in digests:
                results.append({
                    "id": item.id,
                    "date": item.day_date,
                    "service": item.service,
                    "summary": item.summary_text,
                    "contacts": json.loads(item.key_contacts or "[]"),
                    "action_items": json.loads(item.action_items or "[]"),
                    "topics": json.loads(item.key_topics or "[]"),
                    "files": json.loads(item.files_mentioned or "[]"),
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                })
            return results

    def build_brain_context_prompt(self) -> str:
        """Construct a high-density, structured ambient memory block for Jarvis's prompt."""
        now = datetime.now(UTC)
        today_str = now.strftime("%Y-%m-%d")
        seven_days_ago = (now - timedelta(days=self.retention_days)).strftime("%Y-%m-%d")

        hot_events = self.get_hot_events(hours=self.hot_window_hours, limit=40)
        unread_counts = self.get_unread_summary()
        past_digests = self.get_7day_digests(days=self.retention_days)

        lines = [
            f"### 🌐 AMBIENT MULTI-SERVICE MEMORY (7-Day Horizon: {seven_days_ago} to {today_str})",
            f"Active Unread Status (Past 24h): WhatsApp: {unread_counts.get('whatsapp', 0)} unread | Gmail: {unread_counts.get('gmail', 0)} unread | Drive: {unread_counts.get('drive', 0)} updates",
            "",
            "#### ✉️ Recent Gmail Activity (Past 24 Hours):",
        ]

        gmail_events = [e for e in hot_events if e["service"] == "gmail"]
        if not gmail_events:
            lines.append("- No emails received in the past 24 hours.")
        else:
            for evt in gmail_events[:15]:
                status = " [UNREAD]" if evt["is_unread"] else ""
                lines.append(f"- ✉️{status} **{evt['title']}** (From: {evt['sender']}) — {evt['snippet'][:120]}")

        lines.append("")
        lines.append("#### 💬 Recent WhatsApp Activity (Past 3 Days / Active Chats):")
        wa_events = [e for e in hot_events if e["service"] == "whatsapp"]
        if not wa_events:
            lines.append("- No recent WhatsApp chat activity recorded.")
        else:
            for evt in wa_events[:15]:
                status = " [UNREAD]" if evt["is_unread"] else ""
                chat_name = evt["sender"] or "Unknown"
                full_raw = evt.get("full_content")
                msg_summary = ""
                if full_raw:
                    try:
                        p = json.loads(full_raw)
                        msgs = p.get("messages", [])
                        if msgs:
                            recent_texts = []
                            for m in msgs[-3:]:
                                a = m.get("author") or m.get("from") or "User"
                                b = m.get("body") or ("[Media]" if m.get("hasMedia") else "")
                                if b:
                                    recent_texts.append(f"{a}: {b[:60]}")
                            if recent_texts:
                                msg_summary = " | Recent msgs: " + " → ".join(recent_texts)
                    except Exception:
                        pass

                lines.append(f"- 💬{status} **{chat_name}**: {evt['snippet'] or ''}{msg_summary}")

        lines.append("")
        lines.append("#### 📁 Google Drive Updates (Past 24 Hours):")
        drive_events = [e for e in hot_events if e["service"] == "drive"]
        if not drive_events:
            lines.append("- No recent Google Drive file updates recorded.")
        else:
            for evt in drive_events[:10]:
                lines.append(f"- 📁 {evt['sender'] or 'Drive'}: {evt['title']} — {evt['snippet'] or ''}")

        lines.append("")
        lines.append("#### 📅 7-Day Contextual Digests & History:")

        if not past_digests:
            lines.append("- No archived historical digests recorded in the 7-day memory store.")
        else:
            for dg in past_digests[:10]:
                lines.append(f"- **[{dg['date']}] {dg['service'].upper()}**: {dg['summary']}")
                if dg.get("topics"):
                    lines.append(f"  * Key Topics: {', '.join(dg['topics'])}")
                if dg.get("action_items"):
                    lines.append(f"  * Action items: {', '.join(dg['action_items'])}")

        return "\n".join(lines)

    def aggregate_daily_digest(self, day_date: Optional[str] = None) -> None:
        """Compile raw events for a given day into structured daily digests."""
        target_date_str = day_date or datetime.now(UTC).strftime("%Y-%m-%d")

        try:
            target_dt = datetime.strptime(target_date_str, "%Y-%m-%d").replace(tzinfo=UTC)
            day_start = target_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = target_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        except Exception:
            day_start = datetime.now(UTC) - timedelta(hours=24)
            day_end = datetime.now(UTC)

        with SessionLocal() as db:
            repo = Repository(db)
            # Find all events matching the target day window
            events = (
                db.query(ServiceEvent)
                .filter(ServiceEvent.event_timestamp >= day_start, ServiceEvent.event_timestamp <= day_end)
                .all()
            )

            if not events:
                return

            by_service: Dict[str, List[ServiceEvent]] = {"whatsapp": [], "gmail": [], "drive": []}
            for e in events:
                if e.service in by_service:
                    by_service[e.service].append(e)

            for svc, sv_events in by_service.items():
                if not sv_events:
                    continue

                contacts = list({e.sender for e in sv_events if e.sender})
                titles = [e.subject_or_title or "" for e in sv_events if e.subject_or_title]

                if svc == "gmail":
                    summary = f"Processed {len(sv_events)} emails. Key topics: {'; '.join(titles[:5])}. Senders: {', '.join(contacts[:5])}."
                elif svc == "whatsapp":
                    summary = f"Recorded {len(sv_events)} chat interactions with {', '.join(contacts[:5])}."
                else:
                    summary = f"Recorded {len(sv_events)} Google Drive file updates: {', '.join(titles[:4])}."

                repo.upsert_daily_digest(
                    day_date=target_date_str,
                    service=svc,
                    summary_text=summary,
                    key_contacts=contacts[:10],
                    action_items=[],
                    key_topics=[t[:60] for t in titles[:6]],
                    files_mentioned=[],
                )
            logger.info("Aggregated daily memory digest for date: %s", target_date_str)

    def prune_expired(self) -> Dict[str, int]:
        """Execute rolling cleanup according to retention policies."""
        with SessionLocal() as db:
            repo = Repository(db)
            stats = repo.cleanup_expired_service_records(
                event_retention_hours=48,
                digest_retention_days=self.retention_days,
            )
            logger.info("Service memory retention cleanup: %s", stats)
            return stats


# Global singleton instance
_service_memory_manager: Optional[ServiceMemoryManager] = None


def get_service_memory_manager() -> ServiceMemoryManager:
    global _service_memory_manager
    if _service_memory_manager is None:
        _service_memory_manager = ServiceMemoryManager()
    return _service_memory_manager
