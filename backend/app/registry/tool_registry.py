from typing import Dict, Type
from app.core.tool import BaseTool


class ToolRegistry:
    """Registry that holds tool classes keyed by their name.

    Usage:
        registry = ToolRegistry()
        registry.register(MyTool())
        tool = registry.get("my_tool")
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if not isinstance(tool, BaseTool):
            raise TypeError("Only instances of BaseTool can be registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Tool '{name}' is not registered") from exc

    def list_tools(self) -> Dict[str, BaseTool]:
        return self._tools.copy()
