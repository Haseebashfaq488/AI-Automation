from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from .db import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    # Relationship to execution logs
    logs = relationship("ExecutionLog", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Task id={self.id} name={self.name} status={self.status}>"

class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    tool_name = Column(String, nullable=False)
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    success = Column(Integer, nullable=False)  # 1 for success, 0 for failure
    timestamp = Column(DateTime, default=datetime.now(UTC))

    task = relationship("Task", back_populates="logs")

    def __repr__(self) -> str:
        return f"<ExecutionLog id={self.id} tool={self.tool_name} success={self.success}>"


class Memory(Base):
    """Long-term agent memory: durable facts about the user and their preferences."""
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return f"<Memory id={self.id} content={self.content[:40]!r}>"


class ChatMessage(Base):
    """Persisted per-session chat history so conversations survive backend restarts."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)       # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} session={self.session_id} role={self.role}>"


class ServiceEvent(Base):
    """24-Hour Hot Activity Feed event for WhatsApp, Gmail, and Google Drive."""
    __tablename__ = "service_events"

    id = Column(String, primary_key=True, index=True)  # e.g., "wa_msg_123" or "gmail_456"
    service = Column(String(32), nullable=False, index=True)  # "whatsapp" | "gmail" | "drive"
    sender = Column(String(255), nullable=True)
    subject_or_title = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    full_content = Column(Text, nullable=True)
    is_unread = Column(Integer, default=0, index=True)  # 1 for unread, 0 for read
    event_timestamp = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return f"<ServiceEvent id={self.id} service={self.service} sender={self.sender}>"


class ServiceDailyDigest(Base):
    """7-Day Rolling Semantic Memory digests per service."""
    __tablename__ = "service_daily_digests"

    id = Column(Integer, primary_key=True, index=True)
    day_date = Column(String(16), nullable=False, index=True)  # "YYYY-MM-DD"
    service = Column(String(32), nullable=False, index=True)   # "whatsapp" | "gmail" | "drive" | "all"
    summary_text = Column(Text, nullable=False)
    key_contacts = Column(Text, nullable=True)                 # JSON string list
    action_items = Column(Text, nullable=True)                 # JSON string list
    key_topics = Column(Text, nullable=True)                   # JSON string list
    files_mentioned = Column(Text, nullable=True)              # JSON string list
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return f"<ServiceDailyDigest day={self.day_date} service={self.service}>"

