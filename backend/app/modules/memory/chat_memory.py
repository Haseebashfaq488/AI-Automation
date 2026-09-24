"""Short-term chat memory: per-session sliding window of recent messages.

Ultra-fast RAM-first architecture:
- Reads and writes operate directly in RAM (< 0.05ms) for instantaneous conversation turns.
- SQLite persistence (chat_messages table) runs via an asynchronous background write-behind queue.
- Gracefully falls back to pure in-memory operation if SQLite is unavailable.
"""
from __future__ import annotations

import atexit
import logging
import queue
import threading
from typing import Callable, Dict, List, Optional

logger = logging.getLogger("jarvis.memory.chat")


class ChatMemory:
    """Stores the last ``max_messages`` messages per session in RAM with async SQLite write-behind.

    The public API (add / history / clear) is identical and 100% backward compatible.
    """

    def __init__(self, max_messages: int = 20, session_factory: Optional[Callable] = None):
        self.max_messages = max_messages
        self._session_factory = session_factory
        # In-memory RAM store per session — sub-millisecond access
        self._cache: Dict[str, List[dict]] = {}
        self._lock = threading.Lock()
        self._db_available = True

        # Async write-behind queue & worker thread
        self._persist_queue: queue.Queue = queue.Queue()
        self._worker_running = True
        self._worker_thread: Optional[threading.Thread] = None

        self._try_init_db()
        self._start_worker()
        atexit.register(self.flush)

    # ------------------------------------------------------------------
    # Internal DB & Worker helpers
    # ------------------------------------------------------------------

    def _get_db(self):
        """Return a SQLAlchemy session or None if DB is unavailable."""
        if not self._db_available:
            return None
        factory = self._session_factory
        if factory is None:
            try:
                from app.modules.database.db import SessionLocal
                factory = SessionLocal
                self._session_factory = factory
            except Exception:
                self._db_available = False
                return None
        try:
            return factory()
        except Exception:
            self._db_available = False
            return None

    def _try_init_db(self) -> None:
        """Ensure the chat_messages table exists (auto-create via SQLAlchemy)."""
        try:
            from app.modules.database.db import Base, engine
            from app.modules.database.models import ChatMessage  # noqa: F401 — registers model
            Base.metadata.create_all(bind=engine)
        except Exception as exc:
            logger.warning("ChatMemory: SQLite init failed, falling back to RAM: %s", exc)
            self._db_available = False

    def _start_worker(self) -> None:
        """Start daemon thread for non-blocking write-behind SQLite operations."""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._worker_running = True
            self._worker_thread = threading.Thread(
                target=self._persist_loop,
                name="ChatMemory-PersistWorker",
                daemon=True,
            )
            self._worker_thread.start()

    def _persist_loop(self) -> None:
        """Background worker thread draining persistence queue to SQLite in high-speed batches."""
        while self._worker_running:
            try:
                task = self._persist_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if task is None:
                self._persist_queue.task_done()
                break

            tasks = [task]
            # Drain any other immediately available tasks to batch them into one DB transaction
            while len(tasks) < 200:
                try:
                    next_task = self._persist_queue.get_nowait()
                    if next_task is None:
                        break
                    tasks.append(next_task)
                except queue.Empty:
                    break

            db = self._get_db()
            if db is not None:
                try:
                    from app.modules.database.models import ChatMessage
                    from sqlalchemy import func

                    sessions_to_prune: Dict[str, int] = {}
                    for action, args in tasks:
                        if action == "ADD":
                            session_id, role, content, max_msgs = args
                            db.add(ChatMessage(session_id=session_id, role=role, content=content))
                            sessions_to_prune[session_id] = max_msgs
                        elif action == "CLEAR":
                            session_id = args
                            q = db.query(ChatMessage)
                            if session_id is not None:
                                q = q.filter(ChatMessage.session_id == session_id)
                            q.delete(synchronize_session=False)

                    # Batch prune sessions
                    for session_id, max_msgs in sessions_to_prune.items():
                        total = db.query(func.count(ChatMessage.id)).filter(
                            ChatMessage.session_id == session_id
                        ).scalar() or 0
                        overflow = total - max_msgs
                        if overflow > 0:
                            oldest_ids = (
                                db.query(ChatMessage.id)
                                .filter(ChatMessage.session_id == session_id)
                                .order_by(ChatMessage.created_at.asc())
                                .limit(overflow)
                                .all()
                            )
                            ids = [row[0] for row in oldest_ids]
                            if ids:
                                db.query(ChatMessage).filter(ChatMessage.id.in_(ids)).delete(
                                    synchronize_session=False
                                )

                    db.commit()
                except Exception as exc:
                    logger.warning("ChatMemory: Batch DB persist failed: %s", exc)
                    try:
                        db.rollback()
                    except Exception:
                        pass
                finally:
                    db.close()

            for _ in tasks:
                self._persist_queue.task_done()


    def _load_session_from_db(self, session_id: str) -> List[dict]:
        """Load the most recent max_messages rows from DB into RAM cache."""
        db = self._get_db()
        if db is None:
            return []
        try:
            from app.modules.database.models import ChatMessage
            rows = (
                db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.asc())
                .all()
            )
            messages = [{"role": r.role, "content": r.content} for r in rows]
            return messages[-self.max_messages:]
        except Exception as exc:
            logger.warning("ChatMemory: DB read failed: %s", exc)
            return []
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Public API — Ultra-Fast in RAM (< 0.05ms)
    # ------------------------------------------------------------------

    def add(self, session_id: str, role: str, content: str) -> None:
        """Append a message in RAM instantly and enqueue background SQLite persist."""
        with self._lock:
            if session_id not in self._cache:
                self._cache[session_id] = self._load_session_from_db(session_id)
            messages = self._cache[session_id]
            messages.append({"role": role, "content": content})
            if len(messages) > self.max_messages:
                del messages[: len(messages) - self.max_messages]

        # Enqueue non-blocking SQLite persist
        if self._db_available:
            self._persist_queue.put_nowait(("ADD", (session_id, role, content, self.max_messages)))

    def history(self, session_id: str) -> List[dict]:
        """Return a fast in-memory copy of the session's message history (<0.02ms)."""
        with self._lock:
            if session_id not in self._cache:
                self._cache[session_id] = self._load_session_from_db(session_id)
            return list(self._cache[session_id])

    def clear(self, session_id: Optional[str] = None) -> None:
        """Clear session messages in RAM instantly and enqueue DB deletion."""
        with self._lock:
            if session_id is None:
                self._cache.clear()
            else:
                self._cache[session_id] = []

        if self._db_available:
            self._persist_queue.put_nowait(("CLEAR", session_id))


    def flush(self, timeout: float = 2.0) -> None:
        """Wait for pending background SQLite writes to complete (used on test/shutdown)."""
        try:
            self._persist_queue.join()
        except Exception:
            pass

    def close(self) -> None:
        """Stop background worker thread cleanly."""
        self._worker_running = False
        try:
            self._persist_queue.put_nowait(None)
            if self._worker_thread and self._worker_thread.is_alive():
                self._worker_thread.join(timeout=1.0)
        except Exception:
            pass


