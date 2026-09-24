import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EventType(str, Enum):
    # Inbound message digests
    WHATSAPP_INBOUND_DIGEST = "WHATSAPP_INBOUND_DIGEST"
    GMAIL_INBOUND_DIGEST = "GMAIL_INBOUND_DIGEST"
    DRIVE_INBOUND_DIGEST = "DRIVE_INBOUND_DIGEST"

    # Worker lifecycle events
    WORKER_STARTED = "WORKER_STARTED"
    WORKER_STEP_STARTED = "WORKER_STEP_STARTED"
    WORKER_STEP_COMPLETED = "WORKER_STEP_COMPLETED"
    WORKER_VALIDATION_FAILED = "WORKER_VALIDATION_FAILED"
    WORKER_RECOVERY_STARTED = "WORKER_RECOVERY_STARTED"
    WORKER_RECOVERY_COMPLETED = "WORKER_RECOVERY_COMPLETED"
    WORKER_COMPLETED = "WORKER_COMPLETED"
    WORKER_FAILED = "WORKER_FAILED"
    WORKER_BLOCKED = "WORKER_BLOCKED"

    # Task Chaining & Reactive Actions
    TASK_CHAIN_REGISTERED = "TASK_CHAIN_REGISTERED"
    AUTONOMOUS_ACTION_STARTED = "AUTONOMOUS_ACTION_STARTED"
    AUTONOMOUS_ACTION_EXECUTED = "AUTONOMOUS_ACTION_EXECUTED"
    AUTONOMOUS_ACTION_FAILED = "AUTONOMOUS_ACTION_FAILED"

    # System & General notifications
    SYSTEM_NOTIFICATION = "SYSTEM_NOTIFICATION"


class JarvisEvent(BaseModel):
    id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    event_type: EventType
    source: str  # e.g., "whatsapp:listener", "gmail:listener", "worker:opencode", "orchestrator"
    timestamp: float = Field(default_factory=time.time)
    title: str
    summary: str
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_sse_payload(self) -> str:
        """Serialize event to a JSON string suitable for SSE data field."""
        return self.model_dump_json()


class ReactiveHook(BaseModel):
    id: str = Field(default_factory=lambda: f"hook_{uuid.uuid4().hex[:8]}")
    target_session_id: str
    trigger_event: EventType = EventType.WORKER_COMPLETED
    action_tool: str  # e.g., "send_file", "send_message", "send_email", "fork"
    action_params: Dict[str, Any] = Field(default_factory=dict)
    description: str = ""
    created_at: float = Field(default_factory=time.time)
    executed: bool = False
    result: Optional[Any] = None
    error: Optional[Any] = None
    downstream_steps: List[Dict[str, Any]] = Field(default_factory=list)

