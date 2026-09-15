"""Configuration for the OpenCode CLI Worker.

Resolves the ``opencode`` binary path, default model, headless server URL,
and execution controls.
"""
import os
import shutil
from typing import Optional


def get_opencode_binary() -> Optional[str]:
    """Return the path to the ``opencode`` CLI binary, or None if not found."""
    # 1. Explicit env override
    env_bin = os.getenv("OPENCODE_BIN")
    if env_bin and os.path.isfile(env_bin):
        return env_bin

    # 2. Check standard Windows npm global node_modules binary
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        npm_exe = os.path.join(appdata, "npm", "node_modules", "opencode-ai", "bin", "opencode.exe")
        if os.path.isfile(npm_exe):
            return npm_exe
        npm_cmd = os.path.join(appdata, "npm", "opencode.cmd")
        if os.path.isfile(npm_cmd):
            return npm_cmd

    # 3. Check system PATH for real executables
    for candidate in ("opencode.exe", "opencode.cmd", "opencode"):
        path = shutil.which(candidate)
        if path and os.path.isfile(path) and not os.path.isdir(path):
            if candidate == "opencode" and (path.startswith(".") or not os.path.isabs(path)):
                continue
            return path

    return None



def get_opencode_model() -> Optional[str]:
    """Return the OpenCode model identifier (provider/model format), or None to use user default."""
    return os.getenv("OPENCODE_MODEL") or None


def get_opencode_server_url() -> str:
    """Return the URL of a running headless OpenCode server (for ``--attach``)."""
    return os.getenv("OPENCODE_URL", "http://127.0.0.1:4096")


def get_auto_approve() -> bool:
    """Return whether to run OpenCode with ``--auto`` (auto-approve permissions)."""
    return os.getenv("OPENCODE_AUTO", "1") == "1"


def get_milestone_timeout() -> int:
    """Maximum seconds to wait for a single milestone execution."""
    return int(os.getenv("OPENCODE_MILESTONE_TIMEOUT", "300"))


def get_visible_console() -> bool:
    """Return whether to launch OpenCode in a visible Windows terminal window."""
    return os.getenv("OPENCODE_VISIBLE_CONSOLE", "1") == "1"

