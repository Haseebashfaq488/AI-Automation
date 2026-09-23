"""Configuration for the Antigravity CLI Worker (`agy`).

Resolves the `agy` / `antigravity` CLI binary path, models, and execution settings.
"""
from __future__ import annotations

import os
import shutil
from typing import List, Optional

DEFAULT_MODELS = [
    {"id": "gemini-3.8-flash-low", "label": "Gemini 3.8 Flash (Low)", "provider": "google"},
    {"id": "gemini-3.8-flash-medium", "label": "Gemini 3.8 Flash (Medium)", "provider": "google"},
    {"id": "gemini-3.8-flash-high", "label": "Gemini 3.8 Flash (High)", "provider": "google"},
    {"id": "gemini-3.7-flash-low", "label": "Gemini 3.7 Flash (Low)", "provider": "google"},
    {"id": "gemini-3.7-flash-medium", "label": "Gemini 3.7 Flash (Medium)", "provider": "google"},
    {"id": "gemini-3.7-flash-high", "label": "Gemini 3.7 Flash (High)", "provider": "google"},
    {"id": "gemini-3.6-flash-low", "label": "Gemini 3.6 Flash (Low)", "provider": "google"},
    {"id": "gemini-3.6-flash-medium", "label": "Gemini 3.6 Flash (Medium)", "provider": "google"},
    {"id": "gemini-3.6-flash-high", "label": "Gemini 3.6 Flash (High)", "provider": "google"},
    {"id": "gemini-3.1-pro-low", "label": "Gemini 3.1 Pro (Low)", "provider": "google"},
    {"id": "gemini-3.1-pro-high", "label": "Gemini 3.1 Pro (High)", "provider": "google"},
    {"id": "claude-sonnet-4-6", "label": "Claude Sonnet 4.6 (Thinking)", "provider": "anthropic"},
    {"id": "claude-opus-4-6-thinking", "label": "Claude Opus 4.6 (Thinking)", "provider": "anthropic"},
    {"id": "gpt-oss-120b-medium", "label": "GPT-OSS 120B (Medium)", "provider": "openai"},
]


def get_agy_binary() -> Optional[str]:
    """Return the path to the Antigravity CLI binary (`agy` or `antigravity`), or None."""
    # 1. Explicit environment variable override
    env_bin = os.getenv("ANTIGRAVITY_BIN") or os.getenv("ANTIGRAVITY_CLI_PATH") or os.getenv("AGY_PATH")
    if env_bin and os.path.isfile(env_bin):
        return env_bin

    # 2. Check default Windows LocalAppData install location
    local_agy = os.path.expandvars(r"%LOCALAPPDATA%\agy\bin\agy.exe")
    if os.path.isfile(local_agy):
        return local_agy

    # 3. Check standard Windows PATH
    for candidate in ("agy.exe", "agy.cmd", "agy", "antigravity.exe", "antigravity.cmd", "antigravity"):
        path = shutil.which(candidate)
        if path and os.path.isfile(path) and not os.path.isdir(path):
            if not os.path.isabs(path) and path.startswith("."):
                continue
            return path

    return None


def get_antigravity_model(requested_model: Optional[str] = None) -> str:
    """Return the requested model or default to gemini-3.8-flash-low."""
    return (requested_model or os.getenv("ANTIGRAVITY_MODEL") or "gemini-3.8-flash-low").strip()


def get_auto_approve() -> bool:
    """Return whether to run Antigravity CLI with `--auto`."""
    return os.getenv("ANTIGRAVITY_AUTO", "1") == "1"


def get_milestone_timeout() -> int:
    """Maximum seconds to wait for a single milestone execution."""
    return int(os.getenv("ANTIGRAVITY_TIMEOUT", "1800"))


def get_visible_console() -> bool:
    """Return whether to launch Antigravity CLI in a visible Windows terminal window."""
    return os.getenv("ANTIGRAVITY_VISIBLE_CONSOLE", "0") == "1"
