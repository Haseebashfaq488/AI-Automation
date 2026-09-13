from typing import Any, Dict, Set

from app.registry.tool_registry import ToolRegistry


class ScopedToolRegistry:
    """A read‑only view of the global ``ToolRegistry`` that only exposes a
    whitelisted subset of tools.

    This is used by every worker session so that the parent cannot accidentally
    (or maliciously) invoke tools outside the worker's permitted scope.
    """

    def __init__(self, registry: ToolRegistry, allowed: Set[str]):
        self._registry = registry
        self._allowed = allowed

    def get(self, name: str):
        """Return the tool instance if it is in the allowed set, else raise."""
        if name not in self._allowed:
            raise KeyError(f"Tool '{name}' is not allowed for this worker")
        return self._registry.get(name)

    def list_tools(self) -> Dict[str, Any]:
        """Return only the allowed tools (name → tool instance)."""
        return {name: tool for name, tool in self._registry.list_tools().items() if name in self._allowed}

    def allowed_names(self) -> Set[str]:
        """Return the set of permitted tool names."""
        return self._allowed

    def __contains__(self, name: str) -> bool:
        return name in self._allowed