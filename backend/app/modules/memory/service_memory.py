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

        hot_events = self.get_hot_events(hours=self.hot_window_hours, limit=25)
        unread_counts = self.get_unread_summary()
        past_digests = self.get_7day_digests(days=self.retention_days)

        lines = [
            f"### 🌐 AMBIENT MULTI-SERVICE MEMORY (7-Day Horizon: {seven_days_ago} to {today_str})",
            f"Unread Status: WhatsApp ({unread_counts.get('whatsapp', 0)} unread) | Gmail ({unread_counts.get('gmail', 0)} unread) | Drive ({unread_counts.get('drive', 0)} recent)",
            "",
            "#### ⚡ Past 24-Hour Hot Activity Stream:",
        ]

        if not hot_events:
            lines.append("- No recent inbound updates recorded in the past 24 hours.")
        else:
            for evt in hot_events[:15]:
                svc_icon = "💬" if evt["service"] == "whatsapp" else ("✉️" if evt["service"] == "gmail" else "📁")
                status = " [UNREAD]" if evt["is_unread"] else ""
                lines.append(f"- {svc_icon} [{evt['service'].upper()}]{status} {evt['sender'] or 'Unknown'}: {evt['snippet'] or evt['title'] or ''}")

        lines.append("")
        lines.append("#### 📅 7-Day Contextual Digests & History:")

        if not past_digests:
            lines.append("- No archived historical digests recorded in the 7-day memory store.")
        else:
            for dg in past_digests[:10]:
                lines.append(f"- **[{dg['date']}] {dg['service'].upper()}**: {dg['summary']}")
                if dg.get("action_items"):
                    lines.append(f"  * Action items: {', '.join(dg['action_items'])}")
                if dg.get("topics"):
                    lines.append(f"  * Topics: {', '.join(dg['topics'])}")

        return "\n".join(lines)

    def aggregate_daily_digest(self, day_date: Optional[str] = None) -> None:
        """Compile raw events for a given day into structured daily digests."""
        target_date = day_date or datetime.now(UTC).strftime("%Y-%m-%d")

        with SessionLocal() as db:
            repo = Repository(db)
            # Find all events matching the target day
            events = (
                db.query(ServiceEvent)
                .filter(ServiceEvent.created_at.like(f"{target_date}%"))
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
                titles = [e.subject_or_title or e.snippet or "" for e in sv_events[:5]]
                summary = f"Recorded {len(sv_events)} {svc} interactions. Key contacts: {', '.join(contacts[:4])}. Recent: {'; '.join(titles[:3])}"

                repo.upsert_daily_digest(
                    day_date=target_date,
                    service=svc,
                    summary_text=summary,
                    key_contacts=contacts[:10],
                    action_items=[],
                    key_topics=[t[:40] for t in titles[:5]],
                    files_mentioned=[],
                )
            logger.info("Aggregated daily memory digest for date: %s", target_date)

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
