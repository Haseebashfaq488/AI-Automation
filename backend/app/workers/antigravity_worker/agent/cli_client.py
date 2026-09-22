"""Non-interactive Antigravity CLI client.

Wraps `agy run` (or configured CLI) as an async subprocess, streams JSON events,
and preserves session continuity across milestones.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.workers.antigravity_worker.agent import config

logger = logging.getLogger("jarvis.worker.antigravity.cli")


@dataclass
class RunResult:
    """Result of a single `agy run` invocation."""
    success: bool
    session_id: Optional[str] = None
    output_text: str = ""
    events: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


def _build_args(
    *,
    session_id: Optional[str] = None,
    work_dir: Optional[str] = None,
    model: Optional[str] = None,
) -> List[str]:
    """Build the argument list for official Antigravity CLI (`agy.exe`)."""
    binary = config.get_agy_binary()
    if not binary:
        raise FileNotFoundError(
            "Antigravity CLI ('agy.exe') not found. Please verify installation."
        )

    # Use stream-json mode over stdin/stdout pipes (NO prompt in CLI args, zero WinError 206 limits)
    args = [
        binary,
        "--input-format", "stream-json",
        "--output-format", "stream-json",
        "--disable-slash-commands",
    ]

    if session_id:
        args.extend(["--conversation", session_id])

    if model:
        req_m = model.strip()
        effort = None
        for eff in ("low", "medium", "high"):
            if f"-{eff}" in req_m:
                effort = eff
                clean_model = req_m.replace(f"-{eff}", "")
                args.extend(["--model", clean_model])
                args.extend(["--effort", effort])
                break
        if not effort:
            args.extend(["--model", req_m])

    if config.get_auto_approve():
        args.append("--dangerously-skip-permissions")

    return args


def _extract_session_id(events: List[Dict[str, Any]], raw_text: str) -> Optional[str]:
    """Try to extract the Antigravity session/conversation ID from events or raw output."""
    for ev in events:
        sid = (
            ev.get("conversationId")
            or ev.get("conversation_id")
            or ev.get("sessionID")
            or ev.get("session_id")
            or ev.get("sessionId")
            or ev.get("id")
        )
        if sid:
            return str(sid)
        if isinstance(ev.get("response"), dict):
            resp_data = ev["response"]
            if "conversationId" in resp_data:
                return str(resp_data["conversationId"])
            if "id" in resp_data:
                return str(resp_data["id"])
        if isinstance(ev.get("session"), dict) and "id" in ev["session"]:
            return str(ev["session"]["id"])

    # Regex matches
    m = re.search(r"agy_ses_[a-zA-Z0-9]+", raw_text)
    if m:
        return m.group(0)
    m2 = re.search(r'"(?:conversationId|sessionId|session_id)":\s*"([^"]+)"', raw_text)
    if m2:
        return m2.group(1)
    m3 = re.search(r"session[:\s=]+([a-zA-Z0-9_-]+)", raw_text, re.IGNORECASE)
    if m3:
        return m3.group(1)
    # UUID format
    m4 = re.search(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", raw_text)
    if m4:
        return m4.group(0)
    return None


async def run_antigravity_cli(
    prompt: str,
    *,
    session_id: Optional[str] = None,
    work_dir: Optional[str] = None,
    model: Optional[str] = None,
    timeout: Optional[int] = None,
    on_event: Any = None,
) -> RunResult:
    """Execute `agy` via stream-json stdin/stdout and collect structured results."""
    timeout = timeout or config.get_milestone_timeout()

    try:
        args = _build_args(
            session_id=session_id,
            work_dir=work_dir,
            model=model,
        )
    except FileNotFoundError as exc:
        return RunResult(success=False, error=str(exc))

    logger.info("agy run: %s --model %s (prompt_len=%d)", args[0], model or "default", len(prompt))

    def _sync_oneshot() -> Tuple[int, List[Dict[str, Any]], str, Optional[str], Optional[str]]:
        events: List[Dict[str, Any]] = []
        text_parts: List[str] = []
        stderr_text = ""
        extracted_sid = None

        proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=work_dir or "D:/AI-Automation",
            bufsize=1,
        )

        payload = json.dumps({"event": "user", "message": {"content": prompt}}) + "\n"
        proc.stdin.write(payload)
        proc.stdin.flush()

        while True:
            line = proc.stdout.readline()
            if not line:
                break
            line_str = line.strip()
            if not line_str:
                continue
            try:
                ev = json.loads(line_str)
                events.append(ev)

                if not extracted_sid:
                    extracted_sid = ev.get("conversation_id") or ev.get("conversationId")

                event_type = ev.get("event")
                if event_type == "init":
                    continue

                delta = ev.get("step_update", {}).get("text_delta")
                if delta:
                    text_parts.append(str(delta))

                if event_type == "result":
                    res_obj = ev.get("result", {})
                    if not extracted_sid:
                        extracted_sid = res_obj.get("conversation_id")
                    final_resp = res_obj.get("response")
                    if final_resp and not text_parts:
                        text_parts.append(str(final_resp))
                    if res_obj.get("status") == "ERROR" and res_obj.get("error"):
                        stderr_text = str(res_obj.get("error"))
                    break
            except json.JSONDecodeError:
                text_parts.append(line_str)

        try:
            proc.wait(timeout=3.0)
        except Exception:
            proc.terminate()
            proc.wait()

        return proc.returncode, events, "".join(text_parts).strip(), stderr_text or None, extracted_sid

    try:
        returncode, events, output_text, stderr_text, extracted_sid = await asyncio.wait_for(
            asyncio.to_thread(_sync_oneshot),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        return RunResult(
            success=False,
            session_id=session_id,
            output_text="",
            events=[],
            error=f"Execution timed out after {timeout}s",
        )
    except Exception as exc:
        return RunResult(success=False, error=f"Failed to start agy: {exc}")

    if on_event and events:
        for ev in events:
            try:
                res = on_event(ev)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                pass

    has_valid_output = bool(output_text and len(output_text.strip()) > 0)
    success = (returncode == 0) or has_valid_output or not stderr_text

    return RunResult(
        success=success,
        session_id=extracted_sid or session_id,
        output_text=output_text,
        events=events,
        error=stderr_text,
    )


class PersistentAgyDaemon:
    """Maintains a persistent, warm background Antigravity CLI process.

    Uses `agy --input-format stream-json --output-format stream-json` over stdin/stdout pipes,
    eliminating the 10-15s cold-start bootstrap penalty across conversational chat turns.
    """

    def __init__(
        self,
        session_id: str = "jarvis-core-brain",
        model: Optional[str] = None,
        work_dir: str = "D:/AI-Automation",
    ):
        self.session_id = session_id
        self.model = model or "gemini-3.8-flash-low"
        self.work_dir = work_dir
        self.proc: Optional[subprocess.Popen] = None
        self._lock = asyncio.Lock()
        self._is_starting = False

    async def ensure_running(self) -> bool:
        """Start or verify the persistent background daemon process."""
        if self.proc and self.proc.poll() is None:
            return True

        binary = config.get_agy_binary()
        if not binary:
            logger.warning("Antigravity CLI binary not found, cannot start daemon.")
            return False

        args = [
            binary,
            "--input-format", "stream-json",
            "--output-format", "stream-json",
            "--conversation", self.session_id,
            "--disable-slash-commands",
        ]

        # Model & reasoning effort
        model_name = self.model
        for eff in ("low", "medium", "high"):
            if f"-{eff}" in model_name:
                args.extend(["--model", model_name.replace(f"-{eff}", "")])
                args.extend(["--effort", eff])
                break
        else:
            args.extend(["--model", model_name])

        if config.get_auto_approve():
            args.append("--dangerously-skip-permissions")

        try:
            logger.info("Starting Persistent Antigravity CLI Daemon: %s", " ".join(args))
            self.proc = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=self.work_dir,
                bufsize=1,
            )
            return True
        except Exception as exc:
            logger.error("Failed to spawn persistent agy daemon: %s", exc)
            self.proc = None
            return False

    async def send_turn(self, prompt: str, timeout: int = 45) -> RunResult:
        """Send a turn over the persistent stdin/stdout pipe with fallback."""
        async with self._lock:
            running = await self.ensure_running()
            if not running or not self.proc or not self.proc.stdin or not self.proc.stdout:
                logger.info("Persistent daemon unavailable, falling back to one-shot CLI execution.")
                return await run_antigravity_cli(
                    prompt,
                    session_id=self.session_id,
                    work_dir=self.work_dir,
                    model=self.model,
                    timeout=timeout,
                )

            def _sync_exchange() -> Tuple[List[Dict[str, Any]], str]:
                events: List[Dict[str, Any]] = []
                text_parts: List[str] = []

                # Write NDJSON prompt synchronously to persistent daemon's stdin
                payload = json.dumps({"event": "user", "message": {"content": prompt}}) + "\n"
                self.proc.stdin.write(payload)
                self.proc.stdin.flush()

                # Read response lines from stdout
                while True:
                    line = self.proc.stdout.readline()
                    if not line:
                        break
                    line_str = line.strip()
                    if not line_str:
                        continue
                    try:
                        ev = json.loads(line_str)
                        events.append(ev)

                        event_type = ev.get("event")
                        if event_type == "init":
                            continue

                        # Extract text deltas from live step updates
                        delta = ev.get("step_update", {}).get("text_delta")
                        if delta:
                            text_parts.append(str(delta))

                        # Check for turn completion / final result
                        if event_type == "result":
                            res_obj = ev.get("result", {})
                            final_resp = res_obj.get("response")
                            if final_resp and not text_parts:
                                text_parts.append(str(final_resp))
                            break

                    except json.JSONDecodeError:
                        text_parts.append(line_str)

                output_text = "".join(text_parts).strip()
                return events, output_text

            try:
                events, output_text = await asyncio.wait_for(
                    asyncio.to_thread(_sync_exchange),
                    timeout=timeout,
                )

                return RunResult(
                    success=bool(output_text),
                    session_id=self.session_id,
                    output_text=output_text,
                    events=events,
                )

            except asyncio.TimeoutError:
                logger.warning("Persistent daemon turn timed out after %ds, restarting daemon.", timeout)
                await self.stop()
                return await run_antigravity_cli(
                    prompt,
                    session_id=self.session_id,
                    work_dir=self.work_dir,
                    model=self.model,
                    timeout=timeout,
                )
            except Exception as exc:
                logger.warning("Persistent daemon communication error: %s, falling back to one-shot.", exc)
                await self.stop()
                return await run_antigravity_cli(
                    prompt,
                    session_id=self.session_id,
                    work_dir=self.work_dir,
                    model=self.model,
                    timeout=timeout,
                )

    async def stop(self) -> None:
        """Gracefully stop the persistent daemon."""
        if self.proc:
            try:
                if self.proc.stdin:
                    self.proc.stdin.close()
                self.proc.terminate()
                self.proc.wait(timeout=3.0)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            finally:
                self.proc = None



_persistent_daemon: Optional[PersistentAgyDaemon] = None


def get_persistent_agy_daemon() -> PersistentAgyDaemon:
    """Return the global PersistentAgyDaemon instance."""
    global _persistent_daemon
    if _persistent_daemon is None:
        _persistent_daemon = PersistentAgyDaemon()
    return _persistent_daemon

