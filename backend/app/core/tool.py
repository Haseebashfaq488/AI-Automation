from abc import ABC, abstractmethod
from typing import Any, Dict
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BaseTool(ABC):
    """Abstract base class for all filesystem tools.

    Subclasses must define ``name``, ``description`` and ``risk`` attributes and implement
    the ``execute`` coroutine which receives a dictionary of validated parameters.
    """

    name: str
    description: str
    risk: RiskLevel
    input_schema: Dict[str, Any]  # JSON schema for parameters
    category: str = "tool"  # "tool" or "skill"

    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the tool's operation.

        Returns a dictionary that will be wrapped in a ``ToolResult``.
        """
        raise NotImplementedError
