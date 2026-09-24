from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import Task, ExecutionLog, ServiceEvent, ServiceDailyDigest
from typing import Optional, List, Dict, Any
from datetime import datetime, UTC, timedelta
import json

class Repository:
    def __init__(self, db_session: Session):
        self.db = db_session

    # Task operations
    def create_task(self, name: str, status: str = "pending") -> Task:
        task = Task(name=name, status=status)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        return self.db.query(Task).filter(Task.id == task_id).first()

    def update_task_status(self, task_id: int, status: str) -> Optional[Task]:
        task = self.get_task(task_id)
        if task:
            task.status = status
            self.db.commit()
            self.db.refresh(task)
        return task

    def list_tasks(self) -> List[Task]:
        return self.db.query(Task).all()

    # ExecutionLog operations
    def log_execution(
        self,
        tool_name: str,
        input_data: Optional[str] = None,
        output_data: Optional[str] = None,
        success: bool = True,
        task_id: Optional[int] = None,
    ) -> ExecutionLog:
        log = ExecutionLog(
            tool_name=tool_name,
            input_data=input_data,
            output_data=output_data,
            success=1 if success else 0,
            task_id=task_id,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    # ServiceEvent operations (24-Hour Hot Activity Feed)
    def upsert_service_event(
        self,
        event_id: str,
        service: str,
        sender: Optional[str] = None,
        subject_or_title: Optional[str] = None,
        snippet: Optional[str] = None,
        full_content: Optional[str] = None,
        is_unread: bool = False,
        event_timestamp: Optional[datetime] = None,
    ) -> ServiceEvent:
        event = self.db.query(ServiceEvent).filter(ServiceEvent.id == event_id).first()
        ts = event_timestamp or datetime.now(UTC)
        if event:
            if sender is not None:
                event.sender = sender
            if subject_or_title is not None:
                event.subject_or_title = subject_or_title
            if snippet is not None:
                event.snippet = snippet
            if full_content is not None:
                event.full_content = full_content
            event.is_unread = 1 if is_unread else 0
            event.event_timestamp = ts
        else:
            event = ServiceEvent(
                id=event_id,
                service=service,
                sender=sender,
                subject_or_title=subject_or_title,
                snippet=snippet,
                full_content=full_content,
                is_unread=1 if is_unread else 0,
                event_timestamp=ts,
            )
            self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_service_events(
        self,
        service: Optional[str] = None,
        hours: int = 24,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[ServiceEvent]:
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        query = self.db.query(ServiceEvent).filter(ServiceEvent.event_timestamp >= cutoff)
        if service and service.lower() != "all":
            query = query.filter(ServiceEvent.service == service.lower())
        if unread_only:
            query = query.filter(ServiceEvent.is_unread == 1)
        return query.order_by(ServiceEvent.event_timestamp.desc()).limit(limit).all()

    def get_service_unread_counts(self, hours: int = 24) -> Dict[str, int]:
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        rows = (
            self.db.query(ServiceEvent.service, func.count(ServiceEvent.id))
            .filter(ServiceEvent.event_timestamp >= cutoff, ServiceEvent.is_unread == 1)
            .group_by(ServiceEvent.service)
            .all()
        )
        counts = {"whatsapp": 0, "gmail": 0, "drive": 0}
        for svc, cnt in rows:
            counts[svc] = cnt
        return counts

    # ServiceDailyDigest operations (7-Day Rolling Memory)
    def upsert_daily_digest(
        self,
        day_date: str,
        service: str,
        summary_text: str,
        key_contacts: Optional[List[str]] = None,
        action_items: Optional[List[str]] = None,
        key_topics: Optional[List[str]] = None,
        files_mentioned: Optional[List[Dict[str, Any]]] = None,
    ) -> ServiceDailyDigest:
        digest = (
            self.db.query(ServiceDailyDigest)
            .filter(ServiceDailyDigest.day_date == day_date, ServiceDailyDigest.service == service)
            .first()
        )
        kc_json = json.dumps(key_contacts or [])
        ai_json = json.dumps(action_items or [])
        kt_json = json.dumps(key_topics or [])
        fm_json = json.dumps(files_mentioned or [])

        if digest:
            digest.summary_text = summary_text
            digest.key_contacts = kc_json
            digest.action_items = ai_json
            digest.key_topics = kt_json
            digest.files_mentioned = fm_json
            digest.updated_at = datetime.now(UTC)
        else:
            digest = ServiceDailyDigest(
                day_date=day_date,
                service=service,
                summary_text=summary_text,
                key_contacts=kc_json,
                action_items=ai_json,
                key_topics=kt_json,
                files_mentioned=fm_json,
            )
            self.db.add(digest)
        self.db.commit()
        self.db.refresh(digest)
        return digest

    def list_daily_digests(self, days: int = 7, service: Optional[str] = None) -> List[ServiceDailyDigest]:
        cutoff_date = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%d")
        query = self.db.query(ServiceDailyDigest).filter(ServiceDailyDigest.day_date >= cutoff_date)
        if service and service.lower() != "all":
            query = query.filter(ServiceDailyDigest.service == service.lower())
        return query.order_by(ServiceDailyDigest.day_date.desc()).all()

    def cleanup_expired_service_records(self, event_retention_hours: int = 48, digest_retention_days: int = 7) -> Dict[str, int]:
        """Rolling retention cleaner to prune old events and digests."""
        evt_cutoff = datetime.now(UTC) - timedelta(hours=event_retention_hours)
        deleted_events = (
            self.db.query(ServiceEvent)
            .filter(ServiceEvent.event_timestamp < evt_cutoff)
            .delete()
        )
        digest_cutoff = (datetime.now(UTC) - timedelta(days=digest_retention_days)).strftime("%Y-%m-%d")
        deleted_digests = (
            self.db.query(ServiceDailyDigest)
            .filter(ServiceDailyDigest.day_date < digest_cutoff)
            .delete()
        )
        self.db.commit()
        return {"deleted_events": deleted_events, "deleted_digests": deleted_digests}

