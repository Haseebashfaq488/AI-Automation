import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from app.modules.opencode.adapter import OpenCodeAdapter
from app.workers.document_worker.agent.config import (
    get_worker_api_key,
    get_worker_base_url,
    get_worker_model,
)
from app.workers.document_worker.agent.prompts import (
    decision_user_message,
    worker_system_prompt,
)

logger = logging.getLogger("jarvis.worker.agent")


class DocumentWorkerAgent:
    """The document worker's brain.

    Wraps an LLM client (Nemotron via OpenRouter by default, configurable via
    WORKER_MODEL) and turns the worker loop's step history into the next
    tool call. The worker sees only its own compact step results — never the
    parent's conversation (per the parent‑worker design).

    When no API key is configured, ``available`` is False and the engine
    falls back to its deterministic placeholder loop.
    """

    def __init__(self, objective: str, allowed_tools: List[str], fs_scope: str):
        self.objective = objective
        self.allowed_tools = list(allowed_tools)
        self.fs_scope = fs_scope
        self._step_results: List[Dict[str, Any]] = []

        api_key = get_worker_api_key()
        self.available = bool(api_key)
        if self.available:
            self._llm = OpenCodeAdapter(
                api_key=api_key,
                base_url=get_worker_base_url(),
                model=get_worker_model(),
                max_tokens=160,  # decisions are tiny single-step JSON; prevents rate limit exhaustion
            )
            self._system = worker_system_prompt(
                self.allowed_tools, objective, files_in_scope=self._scan_scope(fs_scope)
            )
        else:
            self._llm = None
            self._system = ""

    @staticmethod
    def _scan_scope(fs_scope: str, max_depth: int = 2) -> List[str]:
        """List .docx files under the scope safely (bounded depth, skips noise)."""
        import os
        from pathlib import Path

        try:
            root = Path(fs_scope).resolve()
            if not root.is_dir():
                return []

            ignored_dirs = {
                ".git", ".next", "node_modules", ".venv", "venv",
                "__pycache__", ".pytest_cache", "$recycle.bin",
                "system volume information", "windows", "program files",
                "program files (x86)", "appdata"
            }

            results: List[str] = []
            root_depth = len(root.parts)
            for current_dir, dirs, files in os.walk(str(root)):
                curr_path = Path(current_dir)
                curr_depth = len(curr_path.parts) - root_depth
                if curr_depth >= max_depth:
                    dirs.clear()
                    continue
                dirs[:] = [
                    d for d in dirs
                    if d.lower() not in ignored_dirs and not d.startswith(".") and not d.startswith("$")
                ]
                for f in files:
                    if f.lower().endswith(".docx") and not f.startswith("~$"):
                        results.append(str(curr_path / f))
                        if len(results) >= 20:
                            return results
            return results
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Public API used by the engine loop
    # ------------------------------------------------------------------
    def record_step(self, tool: str, success: bool, output: Any = None, error: Any = None) -> None:
        """Append a compact result the next decision will see."""
        entry: Dict[str, Any] = {"tool": tool, "success": success}
        if error:
            entry["error"] = str(error)[:300]
        elif isinstance(output, dict):
            # Keep only small, decision‑relevant fields
            entry["output"] = {k: v for k, v in output.items() if isinstance(v, (int, float, str, bool))}
            if "paragraphs" in output and isinstance(output["paragraphs"], list):
                texts = [
                    p.get("text", "").strip()
                    for p in output["paragraphs"]
                    if isinstance(p, dict) and p.get("text")
                ]
                if texts:
                    entry["output"]["content_preview"] = " | ".join(texts[:5])[:300]
        self._step_results.append(entry)

    async def decide_next_step(self) -> Dict[str, Any]:
        """Ask the LLM for the next step.

        Returns one of:
          {"action": "tool", "tool": str, "params": dict}
          {"action": "done", "summary": str}
          {"action": "fail", "reason": str}   (LLM unreachable / unparseable)
        """
        if not self.available:
            return {"action": "fail", "reason": "worker LLM not configured"}

        user_msg = decision_user_message(
            self._step_results, f"{self.objective} (fs_scope: {self.fs_scope})"
        )
        # Free tiers throttle per-minute; one patient retry on 429s.
        for attempt in (1, 2):
            try:
                raw = await self._llm._chat(
                    [
                        {"role": "system", "content": self._system},
                        {"role": "user", "content": user_msg},
                    ]
                )
                break
            except Exception as exc:
                detail = str(exc)
                resp = getattr(exc, "response", None)  # httpx.HTTPStatusError
                if resp is not None:
                    detail = f"{detail} | body: {resp.text[:300]}"
                if attempt == 1 and resp is not None and resp.status_code == 429:
                    logger.warning("Worker LLM rate-limited, retrying in 20s: %s", detail)
                    await asyncio.sleep(20)
                    continue
                logger.warning("Worker LLM call failed: %s", detail)
                return {"action": "fail", "reason": f"LLM error: {detail}"}

        decision = self._parse_decision(raw)
        if decision is None:
            return {"action": "fail", "reason": f"Could not parse LLM output: {raw[:200]}"}
        return decision

    def inject_intervention(self, message: str) -> None:
        """Parent guidance arrives as a pseudo‑step so the LLM sees it."""
        self._step_results.append(
            {"tool": "PARENT_GUIDANCE", "success": True, "output": message[:500]}
        )

    # ------------------------------------------------------------------
    # Parsing / validation
    # ------------------------------------------------------------------
    def _parse_decision(self, raw: str) -> Optional[Dict[str, Any]]:
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            # Tolerate stray prose around the JSON object
            start, end = raw.find("{"), raw.rfind("}")
            if start == -1 or end <= start:
                return None
            try:
                parsed = json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                return None

        if not isinstance(parsed, dict):
            return None

        action = parsed.get("action")
        # If action is omitted, infer from tool or summary
        if not action:
            if "tool" in parsed and parsed.get("tool") in self.allowed_tools:
                action = "tool"
            elif "summary" in parsed:
                action = "done"

        if action in ("done", "finish", "completed"):
            return {"action": "done", "summary": str(parsed.get("summary", ""))[:500]}
        if action == "tool":
            tool = parsed.get("tool", "")
            if tool not in self.allowed_tools:
                return {"action": "fail", "reason": f"LLM chose disallowed tool: {tool}"}
            params = parsed.get("params", {})
            if not isinstance(params, dict):
                return None
            params.setdefault("fs_scope", self.fs_scope)
            return {"action": "tool", "tool": tool, "params": params}
        return None