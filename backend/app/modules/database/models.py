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
