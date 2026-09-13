from pydantic import BaseModel, Field
from typing import Any, Optional, Dict
from datetime import datetime, UTC


class ToolResult(BaseModel):
    """Standardized result returned by any tool execution."""

    success: bool = Field(..., description="Whether the tool executed successfully")
    tool: str = Field(..., description="Name of the tool that was executed")
    data: Optional[Dict[str, Any]] = Field(
        None, description="Result payload when success is True"
    )
    error: Optional[Dict[str, Any]] = Field(
        None, description="Error information when success is False"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {"timestamp": datetime.now(UTC).isoformat()},
        description="Additional metadata such as duration, request id, etc.",
    )
