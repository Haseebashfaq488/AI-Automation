"""Jarvis Central Brain Manager powered by Antigravity CLI (`agy.exe`).

Features:
- Living long-term Markdown memory (`JARVIS_MEMORY.md`) read on every turn.
- Persistent session continuity (`--conversation jarvis-core-brain`).
- 10-minute idle auto-checkpointing.
- Direct conversational responses + structured tool planning for WhatsApp, Gmail, File Management, and Background Workers.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.workers.antigravity_worker.agent import config
from app.workers.antigravity_worker.agent.cli_client import run_antigravity_cli
from app.registry.tool_registry import ToolRegistry

logger = logging.getLogger("jarvis.brain.antigravity")

DEFAULT_MEMORY_PATH = Path("D:/AI-Automation/JARVIS_MEMORY.md")
DEFAULT_SESSION_ID = "jarvis-core-brain"
IDLE_CHECKPOINT_SECONDS = 600  # 10 minutes


class JarvisBrainManager:
    """Central orchestrator for Jarvis's persistent Antigravity Brain."""

    _KNOWN_TOOLS = {
        "list_directory": {"path": "absolute path of the directory to list"},
        "exists": {"path": "absolute path to check existence of"},
        "metadata": {"path": "absolute path to get metadata for"},
        "search_files": {"path": "directory to search in", "pattern": "glob pattern to match file names (e.g. *.txt)"},
        "read_file": {"path": "absolute path of the file to read"},
        "create_file": {"path": "absolute path of the new file"},
        "create_folder": {"path": "absolute path of the new folder"},
        "write_file": {"path": "absolute path of the file to write", "content": "file contents"},
        "copy": {"source": "absolute source path", "destination": "absolute destination path"},
        "move": {"source": "absolute source path", "destination": "absolute destination path"},
        "rename": {"source": "absolute path of the file/folder to rename", "destination": "absolute new path"},
        "organize_downloads": {"source_dir": "directory containing the files", "target_dir": "optional destination directory"},
        "search_content": {"path": "file or directory to search in", "query": "text to find inside files"},
        "delete_file": {"path": "absolute path of the file to delete"},
        "delete_folder": {"path": "absolute path of the folder to delete"},
        "archive": {"source": "file or folder to zip", "destination": "absolute path of the .zip archive to create"},
        "extract": {"path": "absolute path of the .zip archive", "destination": "optional folder to extract into"},
        "touch": {"path": "file to create or update the timestamp of"},
        "bulk_rename": {"path": "folder containing the files", "pattern": "new name pattern, use # for a counter"},
        "append_file": {"path": "file to append to", "content": "text to append"},
        "send_message": {"to": "WhatsApp chat name or phone number", "message": "text to send"},
        "send_file": {"to": "WhatsApp chat name or phone number", "path": "absolute path of the local file to send"},
        "list_chats": {},
        "get_messages": {"chat": "WhatsApp chat name or id", "limit": "optional number of messages"},
        "search_messages": {"chat": "WhatsApp chat name or id", "query": "text to search for"},
        "send_report": {"to": "WhatsApp chat name or phone number", "path": "file or folder to summarize and send"},
        "unread_digest": {"to": "optional — chat to send the digest to"},
        "send_email": {"to": "recipient email address", "subject": "optional subject", "body": "email body text", "attachments": "optional list of absolute file paths to attach"},
        "list_recent_emails": {"query": "optional search query (e.g. from:user subject:hello)", "max_results": "optional maximum number of emails"},
        "fork": {"objective": "description of the coding task to fork to the worker"},
    }

    def __init__(
        self,
        memory_path: Optional[Path] = None,
        session_id: str = DEFAULT_SESSION_ID,
        registry: Optional[ToolRegistry] = None,
        model: Optional[str] = None,
    ):
        self.memory_path = memory_path or Path(os.getenv("JARVIS_MEMORY_PATH", str(DEFAULT_MEMORY_PATH)))
        self.session_id = session_id
        self.registry = registry
        self.model = model or os.getenv("JARVIS_BRAIN_MODEL") or "gemini-3.8-flash-low"
        self._last_activity_time = time.time()
        self._checkpoint_task: Optional[asyncio.Task] = None
        self._ensure_memory_file()

    def _ensure_memory_file(self) -> None:
        """Ensure JARVIS_MEMORY.md exists on disk."""
        if not self.memory_path.exists():
            try:
                self.memory_path.parent.mkdir(parents=True, exist_ok=True)
                default_content = (
                    "# 🧠 JARVIS LIVING MEMORY & SYSTEM CONTEXT\n\n"
                    "## 👤 User Profile & Preferences\n"
                    "- **Owner / User**: Haseeb\n"
                    "- **Phone Number**: +923098956995\n"
                    "- **Primary Workspace**: D:/workspace\n\n"
                    "## 🛠️ Integrated Capabilities & Active Tools\n"
                    "- WhatsApp Sidecar (:4097)\n"
                    "- Gmail OAuth (token.json)\n"
                    "- File Management\n"
                    "- Background Workers (D:/workspace)\n"
                )
                self.memory_path.write_text(default_content, encoding="utf-8")
            except Exception as exc:
                logger.warning("Could not initialize memory file %s: %s", self.memory_path, exc)

    def read_memory(self) -> str:
        """Read the full content of JARVIS_MEMORY.md."""
        try:
            if self.memory_path.exists():
                return self.memory_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to read JARVIS_MEMORY.md: %s", exc)
        return ""

    def append_scratchpad(self, note: str) -> bool:
        """Append an entry to the scratchpad section in JARVIS_MEMORY.md."""
        try:
            content = self.read_memory()
            timestamp = time.strftime("%Y-%m-%d %H:%M")
            entry = f"- [{timestamp}] {note.strip()}\n"

            if "## 📝 Scratchpad & Temporary Notes" in content:
                content = content.replace(
                    "## 📝 Scratchpad & Temporary Notes\n",
                    f"## 📝 Scratchpad & Temporary Notes\n{entry}",
                )
            else:
                content += f"\n\n## 📝 Scratchpad & Temporary Notes\n{entry}"

            self.memory_path.write_text(content, encoding="utf-8")
            return True
        except Exception as exc:
            logger.error("Failed to append scratchpad note: %s", exc)
            return False

    def touch_activity(self) -> None:
        """Record activity timestamp to reset idle timer."""
        self._last_activity_time = time.time()

    def _tools_block(self) -> str:
        lines = []
        for name, params in self._KNOWN_TOOLS.items():
            param_desc = ", ".join(f"{k} ({desc})" for k, desc in params.items())
            lines.append(f"- {name}: params: {param_desc}")
        return "\n".join(lines)

    def _check_fast_path(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Evaluate local fast-path intents (<5ms response time)."""
        p = prompt.lower().strip().rstrip("?.!")

        # 1. Greetings
        if p in ("hi", "hello", "hey", "hey jarvis", "hi jarvis", "hello jarvis", "good morning", "good evening", "assalam o alaikum", "aoa", "yo"):
            return {
                "type": "response",
                "message": "Hello Haseeb! I am online and ready to assist you. How can I help with your tasks today?",
            }

        # 2. Profile and Identity Queries
        if any(p == q for q in ("who am i", "what is my name", "what's my name", "who is the owner", "who is the user")):
            return {
                "type": "response",
                "message": "You are Haseeb, the owner and operator of this system.",
            }

        if any(p == q for q in ("what is my phone number", "what's my phone number", "what is my number", "what is my phone")):
            return {
                "type": "response",
                "message": "Your registered phone number is **+923098956995**.",
            }

        if any(p == q for q in ("what is my workspace", "what's my workspace", "where is my workspace", "workspace")):
            return {
                "type": "response",
                "message": "Your primary dedicated workspace is **`D:/workspace`**.",
            }

        if any(p == q for q in ("who are you", "what are you", "what is jarvis", "introduce yourself")):
            return {
                "type": "response",
                "message": (
                    "I am **Jarvis**, your personal AI assistant and autonomous orchestrator powered by the "
                    "Google Antigravity engine. I can manage files, send WhatsApp messages, compose emails, and "
                    "delegate autonomous coding workers in `D:/workspace`."
                ),
            }

        if any(p == q for q in ("what can you do", "what tools do you have", "list your tools", "what tools are available", "show tools", "help")):
            return {
                "type": "response",
                "message": (
                    "Here are my core integrated capabilities:\n"
                    "- 💬 **WhatsApp**: Send messages, send documents, search and list chats\n"
                    "- ✉️ **Gmail**: Send emails with attachments, search inbox\n"
                    "- 📁 **File Management**: Create, edit, move, trash, and archive files in `D:/workspace`\n"
                    "- ⚡ **Autonomous Workers**: Fork complex multi-step coding tasks into dedicated background workers\n"
                    "- 🧠 **Living Memory**: Read and update `JARVIS_MEMORY.md` persistently"
                ),
            }

        if any(p == q for q in ("show memory", "read memory", "view memory", "what is in your memory")):
            mem = self.read_memory()
            return {
                "type": "response",
                "message": f"### 🧠 Jarvis Living Memory (`JARVIS_MEMORY.md`)\n\n{mem}",
            }

        # 3. Explicit Remember Directives (Instant save)
        if any(p.startswith(prefix) for prefix in ("remember that", "remember:", "save note", "keep in mind that", "note that")):
            clean_note = re.sub(r"^(?:remember that|remember:|save note|keep in mind that|note that)\s*", "", prompt, flags=re.IGNORECASE).strip()
            if clean_note:
                self.append_scratchpad(clean_note)
                return {
                    "type": "response",
                    "message": f"I have saved that to my living memory: *\"{clean_note}\"*",
                }

        return None

    def _check_worker_intent(self, prompt: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[Dict[str, Any]]:
        """Detect explicit user requests to delegate or fork a background worker."""
        p = prompt.strip()
        lowered = p.lower()

        worker_triggers = [
            "make a worker", "delegate a task", "delegate task", "delegate to worker",
            "do this task by a worker", "do this by a worker", "run a worker",
            "spawn a worker", "spawn worker", "fork worker", "fork a worker",
            "fork task", "fork the task", "fork this task", "use a worker to",
            "use a worker", "assign a worker", "assign to worker", "worker do this",
            "by a worker", "let a worker", "have a worker",
        ]

        matched = any(trig in lowered for trig in worker_triggers)
        if not matched and not lowered.startswith("fork ") and not lowered.startswith("delegate "):
            return None

        # Extract objective
        objective = ""
        # Sort triggers by descending length to match longest first
        sorted_triggers = sorted(worker_triggers + ["fork", "delegate"], key=len, reverse=True)
        generic_refs = {
            "do this", "do this task", "this", "it", "do this exact task", "do exact task",
            "exact task", "this exact task", "the task", "this task", "that", "do that",
            "do it", "task", "job", "do the job"
        }

        for trig in sorted_triggers:
            if trig in lowered:
                parts = re.split(re.escape(trig), p, flags=re.IGNORECASE, maxsplit=1)
                if len(parts) > 1 and parts[1].strip(" :,-"):
                    candidate = parts[1].strip(" :,-")
                    # Also strip common prefixes like 'to', 'for'
                    candidate_clean = re.sub(r"^(?:to\s+|for\s+|do\s+)", "", candidate, flags=re.IGNORECASE).strip(" :,-")
                    if candidate_clean.lower() not in generic_refs and candidate.lower() not in generic_refs:
                        objective = candidate_clean or candidate
                        break

        # If generic phrase like "make a worker do this exact task", look at recent history
        if not objective or objective.lower() in generic_refs:
            if history:
                for msg in reversed(history):
                    if msg.get("role") == "user" and msg.get("content") and msg.get("content") != prompt:
                        objective = msg["content"].strip()
                        break

        if not objective:
            objective = p

        # Clean prefix
        objective = re.sub(r"^(?:do this exact task[:\s]*|do this task[:\s]*|to[:\s]*|do[:\s]*)", "", objective, flags=re.IGNORECASE).strip() or p

        return {
            "type": "plan",
            "reasoning": f"Fork autonomous Antigravity background worker for: {objective}",
            "steps": [
                {
                    "tool": "fork",
                    "params": {
                        "objective": objective,
                        "fs_scope": "D:/workspace",
                        "worker_type": "antigravity_worker",
                        "max_steps": 20,
                    },
                    "description": f"Launch background worker: {objective}",
                }
            ],
            "plan_id": str(uuid.uuid4()),
        }

    def _is_actionable(self, prompt: str) -> bool:
        """Determine if a prompt requires tool execution planning."""
        p = prompt.lower()
        action_keywords = [
            "send", "whatsapp", "message", "email", "gmail", "inbox",
            "create file", "write file", "make file", "delete", "trash",
            "remove file", "rename", "move", "copy", "organize", "search content",
            "archive", "zip", "extract", "touch", "append", "fork", "delegate",
            "spawn worker", "run worker", "list files", "list directory", "list chats",
        ]
        return any(kw in p for kw in action_keywords)

    def _build_brain_prompt(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        memories: Optional[List[str]] = None,
    ) -> str:
        """Build lean or actionable structured planning prompt."""
        is_actionable = self._is_actionable(prompt)

        history_block = ""
        if history:
            history_lines = [f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in history[-4:]]
            history_block = "## Recent History:\n" + "\n".join(history_lines) + "\n\n"

        if is_actionable:
            tools = self._tools_block()
            return (
                "You are Jarvis, a personal automation assistant. Translate user intent into a tool plan or direct reply.\n\n"
                f"{history_block}"
                f"Available Tools:\n{tools}\n\n"
                "RULES:\n"
                "1. If actionable (file, WhatsApp, Gmail, fork), return a single JSON plan.\n"
                "2. If the user asks to 'fork', plan tool 'fork' with the objective.\n"
                "3. Use absolute paths. Phone number for Haseeb is +923098956995.\n\n"
                "FORMATS:\n"
                '{"type": "response", "message": "<reply>"}\n'
                '{"type": "plan", "reasoning": "<why>", "steps": [{"tool": "<name>", "params": {<params>}, "description": "<desc>"}]}\n\n'
                f"User: {prompt}"
            )
        else:
            # Lean conversational prompt without 30 tool definitions (Ultra-Fast)
            return (
                "You are Jarvis, an intelligent personal AI assistant. "
                "The owner is Haseeb, phone: +923098956995, workspace: D:/workspace.\n\n"
                f"{history_block}"
                "Provide a direct, concise, and helpful response. Return ONLY a JSON object:\n"
                '{"type": "response", "message": "<your answer>"}\n\n'
                f"User: {prompt}"
            )

    def _safe_parse_json(self, raw: str) -> Optional[Dict[str, Any]]:
        """Safely extract JSON object from raw response text."""
        if not raw:
            return None
        text = raw.strip()
        # Remove markdown fences if present
        if "```" in text:
            m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
            if m:
                text = m.group(1).strip()

        try:
            return json.loads(text)
        except Exception:
            pass

        # Try regex extract
        m2 = re.search(r"\{[\s\S]*\}", text)
        if m2:
            try:
                return json.loads(m2.group(0))
            except Exception:
                pass

        return None

    def _required_params(self, tool_name: str) -> List[str]:
        """Return required parameters for a tool from registry or fallback."""
        if self.registry is not None:
            try:
                tool = self.registry.get(tool_name)
                return list(tool.input_schema.get("required", []))
            except KeyError:
                pass
        optional = {
            "target_dir", "recursive", "dry_run", "destination", "case_sensitive",
            "max_results", "permanent", "extension", "start_index",
            "objective", "fs_scope", "allowed_tools", "worker_type", "max_steps",
            "model", "attachments", "subject", "limit",
        }
        spec = self._KNOWN_TOOLS.get(tool_name, {})
        return [k for k in spec if k not in optional]

    def _validate_plan_steps(self, steps: Any) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Validate that all plan steps correspond to valid known tools."""
        if not isinstance(steps, list):
            return [], []
        valid = []
        dropped = []
        for step in steps:
            if not isinstance(step, dict):
                continue
            tool_name = step.get("tool", "")
            if tool_name not in self._KNOWN_TOOLS:
                dropped.append({"tool": tool_name or "?", "reason": "unknown_tool", "missing": []})
                continue
            params = step.get("params", {})
            if not isinstance(params, dict):
                dropped.append({"tool": tool_name, "reason": "bad_params", "missing": []})
                continue
            required = self._required_params(tool_name)
            missing = [k for k in required if k not in params or params[k] in (None, "")]
            if missing:
                dropped.append({"tool": tool_name, "reason": "missing_params", "missing": missing})
                continue
            valid.append({
                "tool": tool_name,
                "params": params,
                "description": step.get("description", tool_name),
            })
        return valid, dropped

    async def analyze_prompt(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        memories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Analyze prompt and return a structured plan or direct response."""
        self.touch_activity()

        # 1. Fast-Path Evaluation (<5ms for common questions & memory updates)
        fast_reply = self._check_fast_path(prompt)
        if fast_reply:
            return fast_reply

        # 2. Worker Intent Evaluation (instant plan generation for worker/delegate prompts)
        worker_plan = self._check_worker_intent(prompt, history=history)
        if worker_plan:
            return worker_plan

        brain_prompt = self._build_brain_prompt(prompt, history=history, memories=memories)

        # 2. Call Antigravity CLI in clean workspace
        try:
            res = await run_antigravity_cli(
                brain_prompt,
                session_id=self.session_id,
                model=self.model,
                work_dir="D:/workspace",
            )
        except Exception as exc:
            logger.error("Antigravity CLI execution error: %s", exc)
            return {
                "type": "response",
                "message": f"I encountered an error communicating with the Antigravity Brain: {exc}",
            }

        if not res.success and not res.output_text:
            return {
                "type": "response",
                "message": f"Antigravity Brain error: {res.error or 'No response received'}",
            }

        parsed = self._safe_parse_json(res.output_text)

        # Handle direct response type
        if parsed and isinstance(parsed, dict) and parsed.get("type") == "response":
            return {"type": "response", "message": parsed.get("message", res.output_text)}

        # Handle plan type
        if parsed and isinstance(parsed, dict) and parsed.get("type") == "plan":
            valid_steps, dropped = self._validate_plan_steps(parsed.get("steps"))
            if valid_steps:
                return {
                    "type": "plan",
                    "reasoning": parsed.get("reasoning", "Executing requested action"),
                    "steps": valid_steps,
                    "plan_id": str(uuid.uuid4()),
                }

        # Fallback: treat response as direct text message
        reply = (parsed.get("message") if isinstance(parsed, dict) and "message" in parsed else None) or res.output_text or "I have processed your request."
        return {"type": "response", "message": reply.strip()}

    async def extract_memories(self, prompt: str, outcome: str, max_facts: int = 3) -> List[str]:
        """Extract durable facts to record in memory."""
        # Auto-append outcome to living scratchpad if meaningful
        if "succeeded" in outcome.lower() or "executed" in outcome.lower():
            self.append_scratchpad(f"Task completed: {prompt} -> {outcome[:120]}")
        return []


# Global singleton instance
_brain_manager: Optional[JarvisBrainManager] = None


def get_brain_manager(registry: Optional[ToolRegistry] = None) -> JarvisBrainManager:
    """Return the global JarvisBrainManager instance."""
    global _brain_manager
    if _brain_manager is None:
        _brain_manager = JarvisBrainManager(registry=registry)
    elif registry is not None and _brain_manager.registry is None:
        _brain_manager.registry = registry
    return _brain_manager
