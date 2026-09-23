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
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.workers.antigravity_worker.agent import config
from app.workers.antigravity_worker.agent.cli_client import get_persistent_agy_daemon, run_antigravity_cli
from app.registry.tool_registry import ToolRegistry

logger = logging.getLogger("jarvis.brain.antigravity")

DEFAULT_MEMORY_PATH = Path(__file__).parent / "JARVIS_MEMORY.md"
DEFAULT_SESSION_ID = "jarvis-core-brain"
IDLE_CHECKPOINT_SECONDS = 600  # 10 minutes


class JarvisBrainManager:
    """Central orchestrator for Jarvis's persistent Antigravity Brain."""

    _KNOWN_TOOLS = {
        # 1. WhatsApp Module (Communication)
        "send_message": {"to": "WhatsApp chat name or phone number", "message": "text to send"},
        "send_file": {"to": "WhatsApp chat name or phone number", "path": "absolute path of the local file to send"},
        "list_chats": {},
        "get_messages": {"chat": "WhatsApp chat name or id", "limit": "optional number of messages"},
        "search_messages": {"chat": "WhatsApp chat name or id", "query": "text to search for"},

        # 2. Gmail Module (Email & Search)
        "send_email": {"to": "recipient email address", "subject": "optional subject", "body": "email body text", "attachments": "optional list of absolute file paths to attach"},
        "list_recent_emails": {"query": "optional search query (e.g. from:user subject:hello)", "max_results": "optional maximum number of emails"},

        # 3. Autonomous Task Delegation & Worker Forking
        "fork": {
            "objective": "Clear description of the engineering, coding, file, or multi-step task to delegate to the worker",
            "fs_scope": "Target workspace directory (default 'D:/workspace')",
            "worker_type": "Worker engine type ('antigravity_worker')",
            "max_steps": "Maximum execution steps (default 20)",
        },
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
        """Append an entry to the scratchpad section in JARVIS_MEMORY.md.

        Deduplicates identical lines and caps the scratchpad at 50 entries so
        the file never grows unbounded (old bug wrote the same line 50+ times).
        """
        try:
            content = self.read_memory()
            timestamp = time.strftime("%Y-%m-%d %H:%M")
            new_line = f"- [{timestamp}] {note.strip()}"

            SECTION = "## 📝 Scratchpad & Temporary Notes"
            MAX_ENTRIES = 50

            if SECTION in content:
                # Split at the FIRST occurrence only to avoid duplicate-section bugs
                pre, _, rest = content.partition(SECTION)
                # rest starts right after the header — collect existing entries
                rest_lines = rest.lstrip("\n").splitlines()
                # Filter to only bullet lines; drop any extra section headers
                existing = [l for l in rest_lines if l.startswith("- ")]
                # Deduplicate: skip if same note (ignoring timestamp) already recorded
                note_body = note.strip()
                if any(note_body in l for l in existing):
                    return True  # already known
                # Prepend new entry and enforce cap
                entries = [new_line] + existing
                entries = entries[:MAX_ENTRIES]
                new_section = SECTION + "\n" + "\n".join(entries) + "\n"
                content = pre + new_section
            else:
                content = content.rstrip() + f"\n\n{SECTION}\n{new_line}\n"

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
            lines.append(f"- `{name}`: params: {param_desc}")
        return "\n".join(lines)

    def _check_fast_path(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Evaluate instant conversational intents (<5ms response time)."""
        p = prompt.lower().strip().rstrip("?.!")

        # 1. Greetings
        if p in ("hi", "hello", "hey", "hey jarvis", "hi jarvis", "hello jarvis", "good morning", "good evening", "assalam o alaikum", "aoa", "yo", "how are you", "how are you doing", "how's it going", "how are you today"):
            return {
                "type": "response",
                "message": "Hello Haseeb! I am doing well and ready to assist you. How can I help with your tasks today?",
            }

        # 2. Profile and Identity Queries
        if p in ("who am i", "what is my name", "what's my name", "who is the owner", "who is the user"):
            return {
                "type": "response",
                "message": "You are Haseeb, the owner and operator of this system.",
            }

        if p in ("what is my phone number", "what's my phone number", "what is my number", "what is my phone"):
            return {
                "type": "response",
                "message": "Your registered phone number is **+923098956995**.",
            }

        if p in ("what is my workspace", "what's my workspace", "where is my workspace", "workspace"):
            return {
                "type": "response",
                "message": "Your primary dedicated workspace is **`D:/workspace`**.",
            }

        if p in ("who are you", "what are you", "what is jarvis", "introduce yourself"):
            return {
                "type": "response",
                "message": (
                    "I am **Jarvis**, your personal AI manager and task coordinator. "
                    "I manage your integrated tools (WhatsApp, Gmail, Files) and delegate coding, document generation, "
                    "and multi-step automation tasks to autonomous background workers in `D:/workspace`."
                ),
            }

        if p in ("what can you do", "what tools do you have", "list your tools", "what tools are available", "show tools", "help"):
            return {
                "type": "response",
                "message": (
                    "Here is my management and delegation model:\n"
                    "- ⚡ **Autonomous Background Workers**: I create and delegate tasks to background workers in `D:/workspace` for you to review and approve\n"
                    "- 💬 **WhatsApp**: Manage chats, send messages and files\n"
                    "- ✉️ **Gmail**: Send emails with attachments and search your inbox\n"
                    "- 📁 **File Operations**: Manage files within `D:/workspace`\n"
                    "- 🧠 **Living Memory**: Read and maintain persistent notes in `JARVIS_MEMORY.md`"
                ),
            }

        if p in ("show memory", "read memory", "view memory", "what is in your memory"):
            mem = self.read_memory()
            return {
                "type": "response",
                "message": f"### 🧠 Jarvis Living Memory (`JARVIS_MEMORY.md`)\n\n{mem}",
            }

        # 3. Explicit Remember Directives
        for prefix in ("remember that ", "remember: ", "save note: ", "note that ", "keep in mind that "):
            if p.startswith(prefix):
                note = prompt.strip()[len(prefix):].strip()
                if note:
                    self.append_scratchpad(note)
                    return {
                        "type": "response",
                        "message": f"I have saved that to my living memory: *\"{note}\"*",
                    }

        return None

    def _build_brain_prompt(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        memories: Optional[List[str]] = None,
    ) -> str:
        """Build structured planning prompt with complete tool knowledge."""
        history_block = ""
        if history:
            history_lines = [f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in history[-10:]]
            history_block = "## Recent Conversation History:\n" + "\n".join(history_lines) + "\n\n"

        memory_text = self.read_memory()
        memory_block = f"## Living Memory & Context:\n{memory_text}\n\n" if memory_text else ""

        # Wire in long-term SQLite facts extracted from previous turns
        ltm_block = ""
        if memories:
            ltm_facts = "\n".join(f"- {m}" for m in memories)
            ltm_block = f"## Long-Term Learned Facts:\n{ltm_facts}\n\n"

        tools = self._tools_block()

        return (
            "You are Jarvis, a personal AI executive manager and task coordinator for Haseeb (Phone: +923098956995, Workspace: D:/workspace).\n\n"
            "### CORE RESPONSIBILITIES & DECISION RULES:\n"
            "1. ORCHESTRATION & TASK DELEGATION: You never write raw code, create files, edit directories, or execute engineering tasks directly in chat text. You coordinate, manage tasks, and plan.\n"
            "2. AUTONOMOUS TASK FORKING (`fork`): Whenever the user asks to create files, write code, build apps, develop scripts, scrape web data, refactor, run terminal commands, test, analyze, or perform ANY file/directory operations, ALWAYS return a plan using the `fork` tool with `objective` set to the task description, `fs_scope` set to 'D:/workspace', and `worker_type` set to 'antigravity_worker'. The forked worker has the full native Antigravity toolkit (write_to_file, replace_file_content, run_command, view_file, list_dir, grep_search, search_web, etc.).\n"
            "3. ATOMIC COMMUNICATION TOOLS: When the user requests an explicit single-step communication operation (WhatsApp send message/file or read chats, Gmail send email with attachments or search inbox), return a plan with that exact tool and the extracted parameters.\n"
            "4. DIRECT CONVERSATION: If the user is asking a conversational question, inquiring about system capabilities, checking task/memory status, or discussing general topics, return a direct `response` object.\n"
            "5. NO PERMISSION ASKING: Never ask 'Would you like me to do that?'. Always return the structured JSON `plan` so the UI presents confirmation buttons directly.\n"
            "6. JSON OUTPUT ONLY: Output must strictly be a single valid JSON object without extra markdown explanations.\n\n"
            f"{memory_block}"
            f"{ltm_block}"
            f"{history_block}"
            f"### AVAILABLE TOOLS & SCHEMAS:\n"
            f"{tools}\n\n"
            "### OUTPUT JSON FORMATS:\n"
            "- For Actions/Plans:\n"
            '{"type": "plan", "reasoning": "<short explanation of tool choice>", "steps": [{"tool": "<tool_name>", "params": {<parameters>}, "description": "<action description>"}]}\n'
            "- For Conversational Responses:\n"
            '{"type": "response", "message": "<direct conversational reply>"}\n\n'
            f"User Prompt: {prompt}"
        )

    def _safe_parse_json(self, raw: str) -> Optional[Dict[str, Any]]:
        """Safely extract JSON object from raw response text."""
        if not raw:
            return None
        text = raw.strip()

        # Handle markdown fences
        if "```" in text:
            first_idx = text.find("```")
            last_idx = text.rfind("```")
            if first_idx != -1 and last_idx != -1 and last_idx > first_idx:
                inner = text[first_idx + 3:last_idx].strip()
                if inner.startswith("json"):
                    inner = inner[4:].strip()
                try:
                    return json.loads(inner)
                except Exception:
                    pass

        try:
            return json.loads(text)
        except Exception:
            pass

        # Extract outer curly braces
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
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
        """Analyze prompt and return a structured plan or direct response via LLM reasoning."""
        self.touch_activity()

        # 1. Fast-Path Evaluation (<5ms for simple greetings, identity, and memory notes)
        fast_reply = self._check_fast_path(prompt)
        if fast_reply:
            return fast_reply

        # 2. Build structured prompt and query Antigravity Brain
        brain_prompt = self._build_brain_prompt(prompt, history=history, memories=memories)

        try:
            daemon = get_persistent_agy_daemon()
            res = await daemon.send_turn(
                brain_prompt,
                timeout=45,
            )
        except Exception as exc:
            err_msg = str(exc)
            logger.error("Antigravity CLI execution error: %s", err_msg)
            if "model output" in err_msg.lower() or "output text or tool calls" in err_msg.lower():
                return {
                    "type": "response",
                    "message": "I was unable to generate a plan for that request. Could you rephrase or provide more details?",
                }
            return {
                "type": "response",
                "message": f"I encountered an error communicating with the Antigravity Brain: {err_msg}",
            }

        if not res.success and not res.output_text:
            err_msg = res.error or "No response received"
            if "model output" in err_msg.lower() or "output text or tool calls" in err_msg.lower():
                return {
                    "type": "response",
                    "message": "The AI model returned an empty response. Please rephrase your request or try again.",
                }
            return {
                "type": "response",
                "message": f"Antigravity Brain error: {err_msg}",
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

    def generate_worker_task_specification(
        self,
        objective: str,
        fs_scope: str = "D:/workspace",
        requirements: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
        success_criteria: Optional[List[str]] = None,
    ) -> str:
        """Synthesize a complete Master Task Specification prompt for autonomous workers."""
        from app.workers.antigravity_worker.agent.milestones import build_master_task_prompt
        return build_master_task_prompt(
            objective=objective,
            fs_scope=fs_scope,
            requirements=requirements,
            constraints=constraints,
            success_criteria=success_criteria,
        )

    def evaluate_worker_completion(
        self,
        session_id: str,
        contract: Any,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate worker execution results against task criteria and produce an executive report."""
        success = result.get("success", False)
        cancelled = result.get("cancelled", False)
        errors = result.get("errors", [])
        tools_used = result.get("tools_used", [])
        output_summary = result.get("output_summary") or result.get("summary") or ""

        if isinstance(contract, dict):
            objective = contract.get("objective") or "Worker task"
        else:
            objective = getattr(contract, "objective", None) or "Worker task"

        if cancelled:
            headline = f"Worker task `{session_id}` was cancelled."
            verdict = "CANCELLED"
        elif success:
            headline = f"Task successfully completed and verified: \"{objective}\""
            verdict = "RESOLVED"
        else:
            err_summary = "; ".join(e.get("message", "") for e in errors) if errors else "Execution encountered errors"
            headline = f"Task execution failed or partially resolved: {err_summary}"
            verdict = "BLOCKED"

        report = {
            "session_id": session_id,
            "verdict": verdict,
            "headline": headline,
            "objective": objective,
            "success": success,
            "steps_completed": result.get("completed_steps", len(tools_used)),
            "errors": errors,
            "summary": output_summary,
        }

        if success:
            self.append_scratchpad(f"Worker [{session_id}] resolved: {objective}")

        return report

    async def extract_memories(self, prompt: str, outcome: str, max_facts: int = 3) -> List[str]:
        """Extract durable facts from a turn via the agy daemon and persist them.

        Sends a lightweight extraction prompt to the persistent agy session.  The
        model returns a JSON list of facts (or an empty list if nothing is worth
        remembering).  Facts are written to both JARVIS_MEMORY.md scratchpad and
        returned for storage in the SQLite LongTermMemory table.
        """
        if not prompt or not outcome:
            return []

        extraction_prompt = (
            "You are a memory extractor for an AI assistant called Jarvis.\n"
            "Given the following conversation turn, extract at most "
            f"{max_facts} durable facts worth remembering long-term about the "
            "user's preferences, patterns, constraints, or system state.\n"
            "Rules:\n"
            "- Only extract facts that will genuinely help Jarvis in FUTURE turns.\n"
            "- Skip trivial one-off requests (e.g. 'create a test file').\n"
            "- Prefer user preferences, corrections, and system configuration facts.\n"
            "- Return ONLY a JSON array of strings, e.g. [\"fact1\", \"fact2\"] or [] if nothing worthy.\n\n"
            f"User prompt: {prompt[:300]}\n"
            f"Outcome: {outcome[:300]}"
        )

        facts: List[str] = []
        try:
            daemon = get_persistent_agy_daemon()
            res = await daemon.send_turn(extraction_prompt, timeout=20)
            if res.output_text:
                raw = res.output_text.strip()
                # Strip markdown fences if present
                if "```" in raw:
                    raw = raw.split("```")[1].strip()
                    if raw.startswith("json"):
                        raw = raw[4:].strip()
                # Parse JSON array
                start = raw.find("[")
                end = raw.rfind("]")
                if start != -1 and end != -1:
                    import json as _json
                    parsed = _json.loads(raw[start:end + 1])
                    if isinstance(parsed, list):
                        facts = [str(f).strip() for f in parsed if f and str(f).strip()]
        except Exception as exc:
            logger.warning("Memory extraction via agy failed: %s", exc)

        # Persist extracted facts to JARVIS_MEMORY.md scratchpad
        for fact in facts:
            self.append_scratchpad(fact)

        return facts


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
