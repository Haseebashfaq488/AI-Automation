"""System control endpoints: Remote shutdown, restart, abort, and power management."""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("jarvis.system")

router = APIRouter(prefix="/system", tags=["system"])


class ShutdownRequest(BaseModel):
    delay_seconds: int = Field(default=10, ge=0, le=300, description="Delay before shutdown in seconds")
    force: bool = Field(default=False, description="Force close running applications")
    message: Optional[str] = Field(
        default="Remote shutdown initiated from Jarvis Control Plane",
        description="Comment displayed to user on Windows",
    )


@router.post("/shutdown")
async def shutdown_system(payload: Optional[ShutdownRequest] = None):
    """Initiate a system shutdown with a safe countdown timer."""
    req = payload or ShutdownRequest()
    delay = req.delay_seconds
    msg = req.message or "Remote shutdown initiated from Jarvis Control Plane"

    try:
        if sys.platform == "win32":
            cmd = ["shutdown", "/s", "/t", str(delay), "/c", msg]
            if req.force:
                cmd.append("/f")
            subprocess.run(cmd, check=True)
        elif sys.platform.startswith("linux") or sys.platform == "darwin":
            # For Linux/macOS, shutdown -h +delay
            delay_min = max(1, delay // 60)
            subprocess.run(["shutdown", "-h", f"+{delay_min}", msg], check=True)
        else:
            raise HTTPException(status_code=501, detail=f"Unsupported platform: {sys.platform}")

        logger.warning("System shutdown initiated (delay=%ds)", delay)
        return {
            "status": "shutdown_scheduled",
            "delay_seconds": delay,
            "message": f"System shutdown scheduled in {delay} seconds. You can cancel with /system/cancel-shutdown.",
        }
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=500, detail=f"Shutdown command failed: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to execute shutdown: {exc}")


@router.post("/restart")
async def restart_system(payload: Optional[ShutdownRequest] = None):
    """Initiate a system restart with a countdown timer."""
    req = payload or ShutdownRequest()
    delay = req.delay_seconds
    msg = req.message or "Remote restart initiated from Jarvis Control Plane"

    try:
        if sys.platform == "win32":
            cmd = ["shutdown", "/r", "/t", str(delay), "/c", msg]
            if req.force:
                cmd.append("/f")
            subprocess.run(cmd, check=True)
        elif sys.platform.startswith("linux") or sys.platform == "darwin":
            delay_min = max(1, delay // 60)
            subprocess.run(["shutdown", "-r", f"+{delay_min}", msg], check=True)
        else:
            raise HTTPException(status_code=501, detail=f"Unsupported platform: {sys.platform}")

        return {
            "status": "restart_scheduled",
            "delay_seconds": delay,
            "message": f"System restart scheduled in {delay} seconds.",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to execute restart: {exc}")


@router.post("/cancel-shutdown")
async def cancel_shutdown():
    """Abort a previously scheduled shutdown or restart."""
    try:
        if sys.platform == "win32":
            subprocess.run(["shutdown", "/a"], check=True)
        elif sys.platform.startswith("linux") or sys.platform == "darwin":
            subprocess.run(["shutdown", "-c"], check=True)
        else:
            raise HTTPException(status_code=501, detail=f"Unsupported platform: {sys.platform}")

        logger.info("System shutdown aborted.")
        return {
            "status": "shutdown_cancelled",
            "message": "System shutdown has been successfully cancelled.",
        }
    except subprocess.CalledProcessError as exc:
        # Code 1116 on Windows = No shutdown was in progress
        return {
            "status": "no_shutdown_active",
            "message": "No active shutdown was in progress or cancel command finished.",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to cancel shutdown: {exc}")


@router.post("/lock")
async def lock_workstation():
    """Lock the Windows workstation immediately."""
    try:
        if sys.platform == "win32":
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
            return {"status": "locked", "message": "Workstation locked."}
        else:
            raise HTTPException(status_code=501, detail="Lock is only implemented for Windows.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to lock workstation: {exc}")
