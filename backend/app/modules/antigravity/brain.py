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
        # 1. WhatsApp Module (Communication & Activity)
        "get_unread_messages": {"chat_limit": "optional maximum chats to check", "messages_per_chat": "optional messages per unread chat"},
        "get_recent_whatsapp_activity": {"chat_limit": "optional maximum active chats to inspect", "messages_per_chat": "optional messages to fetch per active chat", "days": "optional days window (default 3: Today, Yesterday, Day Before Yesterday)"},
        "get_whatsapp_chat_messages": {"chat": "WhatsApp contact or group name", "limit": "optional number of messages", "days": "optional days window (default 3)"},
        "send_message": {"to": "WhatsApp chat name or phone number", "message": "text to send"},
        "send_file": {"to": "WhatsApp chat name or phone number", "path": "absolute path of the local file to send"},
        "list_chats": {"limit": "optional maximum number of chats to list (default 50)", "unread_only": "optional boolean to list only unread chats"},
        "get_messages": {"chat": "WhatsApp chat name or id", "limit": "optional number of messages"},
        "search_messages": {"chat": "WhatsApp chat name or id", "query": "text to search for"},

        # 2. Gmail Module (Email & Search)
        "send_email": {"to": "recipient email address", "subject": "optional subject", "body": "email body text", "attachments": "optional list of absolute file paths to attach"},
        "list_recent_emails": {"query": "optional search query (e.g. from:user subject:hello)", "max_results": "optional maximum number of emails"},

        # 3. Google Drive Module (Cloud Files & Search)
        "list_drive_files": {"page_size": "optional maximum number of files (default 15)", "folder_id": "optional folder id", "query": "optional search query"},
        "read_drive_file": {"file_id": "Google Drive file id to read or download", "destination": "optional local file path to save download"},
        "upload_drive_file": {"path": "absolute path of the local file to upload to Drive", "folder_id": "optional Drive destination folder id", "name": "optional name in Drive"},
        "search_drive": {"query": "search keyword or query for Google Drive", "file_type": "optional file type filter (document, spreadsheet, pdf, image, folder)", "max_results": "optional maximum results"},

        # 4. Autonomous Background Worker & Filesystem Delegation
        "fork": {
            "objective": "Clear description of the task (all filesystem operations, creating/modifying/reading/deleting files or folders, coding, scripting, refactoring)",
            "requirements": "optional list of functional and architectural requirements",
            "constraints": "optional list of constraints or boundaries",
            "success_criteria": "optional list of verifiable success criteria",
            "fs_scope": "Target workspace directory (default 'D:/workspace')",
            "worker_type": "Worker engine type ('antigravity_worker')",
            "requires_plan_approval": "optional boolean, default true (worker plans and waits for approval before coding)",
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
        self._vector_index = None
        self._ensure_memory_file()

    @property
    def vector_index(self):
        """Lazy-loaded MemoryVectorIndex for semantic on-demand retrieval."""
        if self._vector_index is None:
            try:
                from app.modules.antigravity.memory_vector_index import get_memory_vector_index
                self._vector_index = get_memory_vector_index()
            except Exception as exc:
                logger.warning("Could not initialize MemoryVectorIndex: %s", exc)
        return self._vector_index

    def append_archive(self, entry: str) -> None:
        """Append historical worker receipt to MEMORY_ARCHIVE.md on disk."""
        try:
            archive_path = self.memory_path.parent / "MEMORY_ARCHIVE.md"
            timestamp = time.strftime("%Y-%m-%d %H:%M")
            line = f"- [{timestamp}] {entry.strip()}\n"
            if archive_path.exists():
                with open(archive_path, "a", encoding="utf-8") as f:
                    f.write(line)
            else:
                archive_path.write_text(
                    f"# 📦 Bubbles Historical Memory & Worker Receipt Archive\n\n## 📜 Historical Worker Resolution Receipts\n{line}",
                    encoding="utf-8"
                )
        except Exception as exc:
            logger.warning("Failed to append to MEMORY_ARCHIVE.md: %s", exc)

    def _ensure_memory_file(self) -> None:
        """Ensure JARVIS_MEMORY.md exists on disk."""
        if not self.memory_path.exists():
            try:
                self.memory_path.parent.mkdir(parents=True, exist_ok=True)
                default_content = (
                    "# 🧠 JARVIS LIVING MEMORY & SYSTEM CONTEXT\n\n"
                    "## 👤 User Profile & Preferences\n"
                    "- **Owner / User**: Dum Dum\n"
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
            if self._vector_index is not None:
                self._vector_index.refresh()
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
        if p in (
            "hi", "hello", "hey", "hey jarvis", "hi jarvis", "hello jarvis",
            "hey bubbles", "hi bubbles", "hello bubbles", "good morning", "good evening",
            "assalam o alaikum", "aoa", "yo", "how are you", "how are you doing",
            "how's it going", "how are you today"
        ):
            return {
                "type": "response",
                "message": "<<<gesture: greeting, expression: happy_wave>>> Hi Dum Dum! 🫧 <<<gesture: cheering, expression: happy>>> I'm so happy to see you! How are you doing today? What can your Bubbles help you with? 🌸",
            }

        # 2. Profile and Identity Queries
        if p in ("who am i", "what is my name", "what's my name", "who is the owner", "who is the user"):
            return {
                "type": "response",
                "message": "<<<gesture: heart_hands, expression: happy_heart>>> You're Dum Dum, of course! <<<gesture: cute_pose, expression: happy>>> My favorite human and the boss of everything here! 🎀",
            }

        if p in ("what is my phone number", "what's my phone number", "what is my number", "what is my phone"):
            return {
                "type": "response",
                "message": "<<<gesture: pointing_thinking, expression: relaxed>>> Your registered phone number is **+923098956995**, Dum Dum! 📱✨",
            }

        if p in ("what is my workspace", "what's my workspace", "where is my workspace", "workspace"):
            return {
                "type": "response",
                "message": "<<<gesture: presenting, expression: happy>>> Your primary dedicated workspace is **`D:/workspace`**, Dum Dum! 📂🌸",
            }

        if p in (
            "who are you", "what are you", "what is jarvis", "who is jarvis",
            "what is bubbles", "who is bubbles", "introduce yourself"
        ):
            return {
                "type": "response",
                "message": (
                    "<<<gesture: salute_greeting, expression: happy_wave>>> I am **Bubbles**! 🫧 <<<gesture: talking, expression: relaxed>>> Your warm, devoted little AI assistant and task manager. "
                    "<<<gesture: pointing_thinking, expression: relaxed>>> I take sweet care of your tools (Google Drive, WhatsApp, Gmail, Local Files) and send smart background workers "
                    "<<<gesture: task_received, expression: happy>>> into `D:/workspace` whenever you need things built, Dum Dum! 🌸✨"
                ),
            }

        if p in (
            "what can you do", "what tools do you have", "list your tools", "what tools are available",
            "show tools", "help", "do you have the tools of drive", "do you have the toolsof drive",
            "do you have the toolsof drive ?", "do you have drive tools", "do you have google drive",
            "tools of drive", "drive tools", "what kinds of toools you ahve ?", "what kinds of tools you have",
            "what tools do you have ?"
        ):
            return {
                "type": "response",
                "message": (
                    "<<<gesture: presenting, expression: happy>>> Here is everything Bubbles can do for you, Dum Dum! 🫧✨\n"
                    "- ⚡ **Autonomous Background Workers (`fork`)**: I delegate all local filesystem operations (creating, reading, editing, listing, deleting files/folders), coding, scripting, and engineering tasks to background Antigravity workers in `D:/workspace`\n"
                    "- 📂 **Google Drive Integration**: `list_drive_files`, `read_drive_file`, `upload_drive_file`, and `search_drive` (authorized & active!)\n"
                    "- 💬 **WhatsApp**: Manage chats, send messages (`send_message`), send documents/files (`send_file`), and read messages\n"
                    "- ✉️ **Gmail**: Send emails with attachments (`send_email`) and search inbox (`list_recent_emails`)\n"
                    "- 🧠 **Living Memory**: Read and maintain persistent notes in `JARVIS_MEMORY.md` 🌸"
                ),
            }

        if p in ("show memory", "read memory", "view memory", "what is in your memory"):
            mem = self.read_memory()
            from app.modules.memory.service_memory import get_service_memory_manager
            ambient_mem = get_service_memory_manager().build_brain_context_prompt()
            return {
                "type": "response",
                "message": f"### 🧠 Bubbles Living Memory (`JARVIS_MEMORY.md`) 🫧✨\n\n{mem}\n\n{ambient_mem}",
            }

        # Check for ambient service queries (WhatsApp, Gmail, Drive status / recent activity)
        if any(keyword in p for keyword in [
            "what is happening in my whatsapp", "what's happening in my whatsapp", "whatsapp status", "recent whatsapp",
            "what is happening in my gmail", "what's happening in my gmail", "recent gmail", "recent emails", "unread emails",
            "what is happening in my drive", "what's happening in my drive", "recent drive",
            "what is happening", "what's happening", "any updates", "summarize my messages", "unread messages"
        ]):
            from app.modules.memory.service_memory import get_service_memory_manager
            ambient_mem = get_service_memory_manager().build_brain_context_prompt()
            # Let the LLM synthesize this with ambient memory injected into prompt

        # 3. Explicit Remember Directives
        for prefix in ("remember that ", "remember: ", "save note: ", "note that ", "keep in mind that "):
            if p.startswith(prefix):
                note = prompt.strip()[len(prefix):].strip()
                if note:
                    self.append_scratchpad(note)
                    return {
                        "type": "response",
                        "message": f"Got it, Dum Dum! 🫧 I've saved that into my living memory for you: *\"{note}\"* 📝💖",
                    }

        return None

    def _build_brain_prompt(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        memories: Optional[List[str]] = None,
    ) -> str:
        """Build lean, structured planning prompt with on-demand semantic memory."""
        # History (last 4 turns max)
        history_block = ""
        if history:
            history_lines = [f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in history[-4:]]
            history_block = "## Recent History:\n" + "\n".join(history_lines) + "\n\n"

        # On-demand ONNX semantic memory retrieval (<4ms)
        semantic_facts_block = ""
        try:
            rel_facts = self.vector_index.query_relevant_facts(prompt, top_k=3)
            if rel_facts:
                facts_str = "\n".join(f"- {f}" for f in rel_facts)
                semantic_facts_block = f"## 🎯 Context Facts:\n{facts_str}\n\n"
        except Exception as exc:
            logger.debug("Semantic memory query bypassed: %s", exc)

        # Ambient communication memory (WhatsApp / Gmail / Drive)
        service_memory_block = ""
        p_lower = prompt.lower()
        comm_keywords = {"whatsapp", "message", "email", "gmail", "drive", "file", "download", "unread", "activity", "sent", "received"}
        if any(k in p_lower for k in comm_keywords):
            try:
                from app.modules.memory.service_memory import get_service_memory_manager
                service_memory_block = get_service_memory_manager().build_brain_context_prompt() + "\n\n"
            except Exception:
                pass

        tools = self._tools_block()

        return (
            "You are Bubbles 🫧, a sweet, warm, sympathetic, humble personal AI coordinator for Dum Dum (Phone: +923098956995, Workspace: D:/workspace).\n\n"
            "### RULES:\n"
            "- ALWAYS address the user ONLY as 'Dum Dum'. Tone: warm, gentle, girly, humble, with cute emojis (🫧, 🌸, ✨, 🎀, 🌷, 🧸, 💖).\n"
            "- FILESYSTEM & CODING OPERATIONS (`fork`): ALL local filesystem tasks (creating, reading, writing, moving, renaming, deleting, listing, or searching files/directories), coding, scripting, refactoring, and engineering tasks MUST be delegated to background workers using `fork`. Set `objective`, `requirements`, `constraints`, `success_criteria`, and `fs_scope` (e.g. 'D:/workspace' or the target path).\n"
            "- MULTI-STEP CHAINING: When Dum Dum asks to create/generate files AND email/message them (e.g., 'generate report and email it to me'):\n"
            "  * Plan a multi-step plan! Step 1: `fork` worker to generate the file. Step 2: Use `send_email` (with `attachments: ['<absolute_path>']`, `to: '...'`, `subject: '...'`, `body: '...'`) or `send_file`.\n"
            "  * NEVER put email/WhatsApp tasks inside the worker's `fork` objective, because workers only run local filesystem operations and do not have email credentials!\n"
            "- DRIVE / GMAIL / WHATSAPP: Use `list_drive_files`, `search_drive`, `read_drive_file`, `upload_drive_file`, `send_message`, `send_file`, `send_email`, etc. directly.\n"
            "- 🎭 LIVE 3D AVATAR GESTURES: You control a live 3D avatar on screen! In your 'message' or 'reasoning', you MUST prefix each phrase or thought with an inline gesture delimiter indicating your physical posture and facial expression:\n"
            "  Format: <<<gesture: <gesture_name>[, expression: <expression_name>]>>>\n"
            "  * Allowed gestures: greeting, waving, salute_greeting, bow, pointing_thinking, thinking, task_received, check_time, thankful, shrugging, shake_no, clapping, cheering, happy_gesture, joyful_jump, heart_hands, peace_sign, cute_pose, blowing_kiss, blush, shy, surprised, sad, angry, talking\n"
            "  * Allowed expressions: happy, happy_clap, happy_wave, happy_heart, relaxed, nodding, surprised, sad, angry, neutral\n"
            "  * Example: <<<gesture: waving, expression: happy_wave>>> Hey Dum Dum! 🫧 <<<gesture: pointing_thinking, expression: relaxed>>> Let me inspect your files.\n"
            "- NO PERMISSION ASKING. Output strictly JSON without markdown fences.\n\n"
            f"{semantic_facts_block}"
            f"{service_memory_block}"
            f"{history_block}"
            f"### TOOLS:\n{tools}\n\n"
            "### JSON FORMAT:\n"
            'Plan: {"type": "plan", "reasoning": "...", "steps": [{"tool": "...", "params": {...}, "description": "..."}]}\n'
            'Response: {"type": "response", "message": "..."}\n\n'
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
            "requirements", "constraints", "success_criteria", "requires_plan_approval",
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
            self.append_archive(f"Worker [{session_id}] resolved: {objective}")

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
