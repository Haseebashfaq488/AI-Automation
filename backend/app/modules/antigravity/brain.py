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

    def _build_brain_prompt(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        memories: Optional[List[str]] = None,
    ) -> str:
        """Build structured planning prompt embedding memory and available tools."""
        memory_content = self.read_memory()
        tools = self._tools_block()

        history_block = ""
        if history:
            history_lines = [f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in history[-6:]]
            history_block = "## Recent Conversation History:\n" + "\n".join(history_lines) + "\n\n"

        return (
            "You are Jarvis, a personal automation assistant. You can manage files, "
            "send WhatsApp messages and files, and send/list emails via Gmail, and fork background worker tasks.\n\n"
            "## LIVING SYSTEM MEMORY (JARVIS_MEMORY.md):\n"
            f"{memory_content}\n\n"
            f"{history_block}"
            f"Available tools and their required params:\n{tools}\n\n"
            "RULES:\n"
            "1. If the prompt is NOT an actionable operation (greeting, question, "
            "conversation, asking about memory, checking status), return a direct conversational response.\n"
            "2. If the user asks to remember or save information (e.g. 'remember my email is ...', 'save note ...'), "
            "acknowledge that you will store it in memory and answer conversationally.\n"
            "3. If the prompt IS an actionable operation (file, WhatsApp, or email), plan the exact steps needed.\n"
            "4. If the user says 'fork', 'delegate', or 'spawn a worker', plan a single step with the 'fork' tool "
            "with objective set to the task description.\n"
            "5. Use absolute paths for files. Never invent paths or phone numbers — use memory context.\n\n"
            "RESPONSE FORMATS (Return ONLY one valid JSON object, no markdown codeblocks):\n\n"
            "For non-actionable prompts (greetings, questions, conversational answers):\n"
            '{"type": "response", "message": "<your conversational reply>"}\n\n'
            "For actionable prompts:\n"
            '{"type": "plan", "reasoning": "<brief explanation of what you will do>", '
            '"steps": [{"tool": "<tool_name>", "params": {<params>}, '
            '"description": "<short human-readable description of this step>"}]}\n\n'
            f"User Prompt: {prompt}"
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

        # Check for explicit memory update directive
        lowered = prompt.lower().strip()
        if any(lowered.startswith(p) for p in ("remember that", "remember:", "save note", "keep in mind that", "note that")):
            clean_note = re.sub(r"^(?:remember that|remember:|save note|keep in mind that|note that)\s*", "", prompt, flags=re.IGNORECASE)
            self.append_scratchpad(clean_note)

        brain_prompt = self._build_brain_prompt(prompt, history=history, memories=memories)

        # Call Antigravity CLI with persistent session ID
        try:
            res = await run_antigravity_cli(
                brain_prompt,
                session_id=self.session_id,
                model=self.model,
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
