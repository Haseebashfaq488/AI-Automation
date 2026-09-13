from typing import Dict, Any
from app.core.execution_engine import ExecutionEngine
from app.registry import registry
from app.modules.gmail.skills.list_recent_emails import ListRecentEmailsSkill


class ListRecentEmailsPipeline:
    """Pipeline that runs the ListRecentEmailsSkill.

    Demonstrates how higher‑level pipelines can orchestrate skills.
    """

    def __init__(self):
        self.engine = ExecutionEngine(registry)

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.engine.run(ListRecentEmailsSkill.name, params)
        return {
            "pipeline": "list_recent_emails",
            "success": result.success,
            "result": result.data,
            "error": result.error,
        }