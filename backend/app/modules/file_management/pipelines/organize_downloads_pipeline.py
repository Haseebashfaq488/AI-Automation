from typing import Dict, Any
from app.core.execution_engine import ExecutionEngine
from app.registry import registry
from app.modules.file_management.skills.organize_downloads import OrganizeDownloadsSkill


class OrganizeDownloadsPipeline:
    """Pipeline that runs the OrganizeDownloadsSkill.

    It demonstrates how higher‑level pipelines can orchestrate multiple
    skills/tools. Currently it only runs a single skill but can be extended
    with additional steps.
    """

    def __init__(self):
        self.engine = ExecutionEngine(registry)

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Directly invoke the skill via the execution engine
        result = await self.engine.run(OrganizeDownloadsSkill.name, params)
        return {
            "pipeline": "organize_downloads",
            "success": result.success,
            "result": result.data,
            "error": result.error,
        }
