import sys
import subprocess
from typing import Any, Dict
from app.core.tool import BaseTool, RiskLevel


class CancelShutdownTool(BaseTool):
    name = "cancel_shutdown"
    description = "Cancel or abort a previously scheduled system shutdown or restart."
    risk = RiskLevel.LOW
    category = "tool"
    input_schema = {
        "type": "object",
        "properties": {},
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if sys.platform == "win32":
                subprocess.run(["shutdown", "/a"], check=True)
            elif sys.platform.startswith("linux") or sys.platform == "darwin":
                subprocess.run(["shutdown", "-c"], check=True)
            else:
                raise RuntimeError(f"Unsupported OS: {sys.platform}")

            return {
                "status": "shutdown_cancelled",
                "message": "System shutdown has been successfully cancelled.",
            }
        except subprocess.CalledProcessError:
            return {
                "status": "no_shutdown_active",
                "message": "No active shutdown was in progress.",
            }
