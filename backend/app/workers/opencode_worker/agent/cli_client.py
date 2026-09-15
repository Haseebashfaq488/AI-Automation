"""Non-interactive OpenCode CLI client.

Wraps ``opencode run`` as an async subprocess, streams JSON events,
and preserves session continuity across milestones.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from app.workers.opencode_worker.agent import config

logger = logging.getLogger("jarvis.worker.opencode.cli")


@dataclass
class RunResult:
    """Result of a single ``opencode run`` invocation."""
    success: bool
    session_id: Optional[str] = None
    output_text: str = ""
    events: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


def _build_args(
    prompt: str,
    *,
    session_id: Optional[str] = None,
    work_dir: Optional[str] = None,
    model: Optional[str] = None,
    json_format: bool = True,
) -> List[str]:
    """Build the ``opencode run`` argument list."""
    binary = config.get_opencode_binary()
    if not binary:
        raise FileNotFoundError("opencode CLI not found on PATH")

    args = [binary, "run", prompt]

    if session_id:
        args.extend(["--session", session_id])

    if work_dir:
        args.extend(["--dir", work_dir])

    resolved_model = model or config.get_opencode_model()
    if resolved_model:
        args.extend(["--model", resolved_model])

    if json_format:
        args.extend(["--format", "json"])

    if config.get_auto_approve():
        args.append("--auto")

    return args


import os
import subprocess
import sys
import tempfile


def _run_subprocess_sync(
    args: List[str],
    work_dir: Optional[str],
    timeout: int,
    visible_console: bool = False,
) -> tuple[int, List[Dict[str, Any]], str, str]:
    """Execute opencode in a thread worker (optionally in a visible Windows terminal window)."""
    events: List[Dict[str, Any]] = []
    raw_parts: List[str] = []

    # ── 1. Visible Console Window on Windows ─────────────────────────────
    if sys.platform == "win32" and visible_console:
        fd, temp_log = tempfile.mkstemp(suffix=".log", prefix="opencode_run_")
        os.close(fd)
        fd2, runner_py = tempfile.mkstemp(suffix=".py", prefix="opencode_runner_")
        os.close(fd2)

        runner_content = f"""
import os, sys, subprocess

os.system('title Jarvis Worker: OpenCode CLI')
args = {repr(args)}
work_dir = {repr(work_dir)}
log_path = {repr(temp_log)}

print("=" * 65)
print("  JARVIS AGENT -> OpenCode CLI Worker (Live Execution)")
print("=" * 65)
print()

with open(log_path, 'w', encoding='utf-8') as lf:
    proc = subprocess.Popen(
        args,
        cwd=work_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        shell=False,
    )
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        lf.write(line)
        lf.flush()
    proc.wait()
    sys.exit(proc.returncode)
"""
        try:
            with open(runner_py, "w", encoding="utf-8") as rf:
                rf.write(runner_content)

            proc = subprocess.Popen(
                ["cmd.exe", "/c", "start", "Jarvis Worker: OpenCode CLI", "/wait", sys.executable, runner_py],
                shell=False,
            )

            try:
                proc.wait(timeout=timeout)
                returncode = proc.returncode
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                return -1, events, "", f"Milestone timed out after {timeout}s"

            if os.path.exists(temp_log):
                with open(temp_log, "r", encoding="utf-8", errors="replace") as lf:
                    for line in lf:
                        line_str = line.strip()
                        if not line_str:
                            continue
                        try:
                            ev = json.loads(line_str)
                            events.append(ev)
                            content = (
                                ev.get("content")
                                or ev.get("text")
                                or (ev.get("part", {}).get("text") if isinstance(ev.get("part"), dict) else None)
                                or ev.get("message")
                                or ""
                            )
                            if content:
                                raw_parts.append(str(content))
                            else:
                                raw_parts.append(line_str)
                        except json.JSONDecodeError:
                            events.append({"type": "text", "content": line_str})
                            raw_parts.append(line_str)

            return returncode, events, "\n".join(raw_parts), ""
        finally:
            for p in (temp_log, runner_py):
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass

    # ── 2. Headless execution ───────────────────────────────────────────
    proc = subprocess.Popen(
        args,
        cwd=work_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )

    try:
        if proc.stdout:
            for line in proc.stdout:
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    ev = json.loads(line_str)
                    events.append(ev)
                    content = (
                        ev.get("content")
                        or ev.get("text")
                        or (ev.get("part", {}).get("text") if isinstance(ev.get("part"), dict) else None)
                        or ev.get("message")
                        or ""
                    )
                    if content:
                        raw_parts.append(str(content))
                    else:
                        raw_parts.append(line_str)
                except json.JSONDecodeError:
                    events.append({"type": "text", "content": line_str})
                    raw_parts.append(line_str)

        stdout_rest, stderr_text = proc.communicate(timeout=timeout)
        if stdout_rest:
            raw_parts.append(stdout_rest)
        return proc.returncode, events, "\n".join(raw_parts), (stderr_text or "").strip()
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        return -1, events, "\n".join(raw_parts), f"Milestone timed out after {timeout}s"
    except Exception as exc:
        proc.kill()
        proc.communicate()
        return -1, events, "\n".join(raw_parts), f"Execution error: {exc}"


def _extract_session_id(events: List[Dict[str, Any]], raw_text: str) -> Optional[str]:
    """Try to extract the OpenCode session ID from events or raw output."""
    for ev in events:
        sid = ev.get("sessionID") or ev.get("session_id") or ev.get("sessionId")
        if sid:
            return str(sid)
        if isinstance(ev.get("session"), dict) and "id" in ev["session"]:
            return str(ev["session"]["id"])
    # Fallback: parse session ID from raw text
    m = re.search(r"ses_[a-zA-Z0-9]+", raw_text)
    if m:
        return m.group(0)
    m2 = re.search(r"session[:\s=]+([a-zA-Z0-9_-]+)", raw_text, re.IGNORECASE)
    if m2:
        return m2.group(1)
    return None



async def run_opencode(
    prompt: str,
    *,
    session_id: Optional[str] = None,
    work_dir: Optional[str] = None,
    model: Optional[str] = None,
    timeout: Optional[int] = None,
    on_event: Any = None,
) -> RunResult:
    """Execute ``opencode run`` and collect structured results.

    Parameters
    ----------
    prompt:
        The milestone prompt to send.
    session_id:
        Existing OpenCode session ID for continuity.  None = new session.
    work_dir:
        The project directory (``--dir``).
    model:
        Override the default model.
    timeout:
        Max seconds to wait.  Defaults to ``OPENCODE_MILESTONE_TIMEOUT``.
    on_event:
        Optional async callback ``(event_dict) -> None`` for real-time streaming.

    Returns
    -------
    RunResult with success flag, parsed events, and extracted session ID.
    """
    timeout = timeout or config.get_milestone_timeout()

    try:
        args = _build_args(
            prompt,
            session_id=session_id,
            work_dir=work_dir,
            model=model,
        )
    except FileNotFoundError as exc:
        return RunResult(success=False, error=str(exc))

    logger.info("opencode run: %s", " ".join(args[:6]) + " ...")

    try:
        returncode, events, raw_text, stderr_text = await asyncio.to_thread(
            _run_subprocess_sync,
            args,
            work_dir,
            timeout,
            config.get_visible_console(),
        )
    except Exception as exc:
        return RunResult(success=False, error=f"Failed to start opencode: {exc}")

    if on_event and events:
        for ev in events:
            try:
                res = on_event(ev)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                pass

    extracted_sid = _extract_session_id(events, raw_text)
    success = returncode == 0
    error = stderr_text if not success and stderr_text else None

    return RunResult(
        success=success,
        session_id=extracted_sid or session_id,
        output_text=raw_text,
        events=events,
        error=error,
    )
