import sys
import subprocess
from typing import Any, Dict
from app.core.tool import BaseTool, RiskLevel


class ShutdownTool(BaseTool):
    name = "shutdown_system"
    description = (
        "Shut down the host PC gracefully. Allows setting delay_seconds (default 10) "
        "and force (default false). Shutdown can be aborted before countdown expires."
    )
    risk = RiskLevel.HIGH
    category = "tool"
    input_schema = {
        "type": "object",
        "properties": {
            "delay_seconds": {
                "type": "integer",
                "description": "Seconds to wait before shutting down (default 10)",
                "default": 10,
            },
            "force": {
                "type": "boolean",
                "description": "Force close running applications without prompting",
                "default": False,
            },
            "message": {
                "type": "string",
                "description": "Shutdown reason or comment",
                "default": "Remote shutdown initiated from Jarvis",
            },
        },
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        delay = int(params.get("delay_seconds", 10))
        force = bool(params.get("force", False))
        msg = str(params.get("message", "Remote shutdown initiated from Jarvis"))

        if sys.platform == "win32":
            cmd = ["shutdown", "/s", "/t", str(delay), "/c", msg]
            if force:
                cmd.append("/f")
            subprocess.run(cmd, check=True)
        elif sys.platform.startswith("linux") or sys.platform == "darwin":
            delay_min = max(1, delay // 60)
            subprocess.run(["shutdown", "-h", f"+{delay_min}", msg], check=True)
        else:
            raise RuntimeError(f"Unsupported OS: {sys.platform}")

        return {
            "status": "shutdown_scheduled",
            "delay_seconds": delay,
            "message": f"System shutdown scheduled in {delay} seconds.",
        }
