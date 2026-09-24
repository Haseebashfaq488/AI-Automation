"""Long-term memory: durable facts persisted in SQLite.

These survive restarts and are injected into the agent's planning prompt as
"known facts" so preferences and important paths follow the user across
sessions.
"""
from typing import Callable, List, Optional

from app.modules.database.db import SessionLocal
from app.modules.database.models import Memory


class LongTermMemory:
    """SQLite-backed store of durable facts (deduplicated, capped)."""

    def __init__(self, limit: int = 100, session_factory: Optional[Callable] = None):
        self.limit = limit
        self._session_factory = session_factory or SessionLocal

    def add(self, content: str) -> bool:
        """Add a fact. Returns False if empty or already known."""
        content = (content or "").strip()
        if not content:
            return False
        db = self._session_factory()
        try:
            existing = db.query(Memory).filter(Memory.content == content).all()
            if existing:
                return False
            # enforce cap by dropping the oldest fact
            count = db.query(Memory).count()
            if count >= self.limit:
                oldest = db.query(Memory).order_by(Memory.created_at.asc()).first()
                if oldest is not None:
                    db.delete(oldest)
            db.add(Memory(content=content))
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


    def all(self, limit: int = 20) -> List[str]:
        """Return up to ``limit`` most recent facts (oldest first)."""
        db = self._session_factory()
        try:
            rows = db.query(Memory).order_by(Memory.created_at.desc()).limit(limit).all()
            return [r.content for r in reversed(rows)]
        finally:
            db.close()

    def search(self, query: str, limit: int = 10) -> List[str]:
        """Case-insensitive substring search over stored facts."""
        db = self._session_factory()
        try:
            rows = (
                db.query(Memory)
                .filter(Memory.content.ilike(f"%{query}%"))
                .order_by(Memory.created_at.desc())
                .limit(limit)
                .all()
            )
            return [r.content for r in rows]
        finally:
            db.close()

    def remember(self, content: str, category: Optional[str] = None) -> bool:
        """Alias for add."""
        return self.add(content)

    def recall(self, limit: int = 20) -> List[str]:
        """Alias for all."""
        return self.all(limit=limit)

    def forget(self, content: str) -> bool:
        """Remove a specific fact by exact content match."""
        content = (content or "").strip()
        if not content:
            return False
        db = self._session_factory()
        try:
            row = db.query(Memory).filter(Memory.content == content).first()
            if row:
                db.delete(row)
                db.commit()
                return True
            return False
        finally:
            db.close()

    def clear(self) -> int:
        """Remove all facts. Returns how many were deleted."""
        db = self._session_factory()
        try:
            count = db.query(Memory).count()
            db.query(Memory).delete()
            db.commit()
            return count
        finally:
            db.close()

