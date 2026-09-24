import httpx
import json
import os
import uuid
from typing import Any, Dict, List, Optional

from app.registry.tool_registry import ToolRegistry


class OpenCodeAdapter:
    """Adapter to communicate with the Groq LLM and translate prompts into tool plans.

    This class provides a simple async interface to send a prompt to the
    Groq LLM and retrieve either:
      - a direct conversational response, or
      - a structured plan listing the tools to execute.

    The planning flow is two-phase:
      1. ``analyze_prompt`` returns a plan (or direct response) for the user to review.
      2. The caller executes the plan steps via the execution engine.
    """

    # Tool names we want the LLM to choose from (subset of the registry).
    # NOTE: params must match each tool's ``input_schema`` exactly — the plan
    # validator below drops any step whose params do not satisfy the schema.
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
        "rename": {"source": "absolute path of the file/folder to rename", "destination": "absolute new path (same folder, different name)"},
        "organize_downloads": {"source_dir": "directory containing the files to organize", "target_dir": "(optional) destination base directory; organized in-place if omitted"},
        "search_content": {"path": "file or directory to search in", "query": "text to find inside files"},
        "delete_file": {"path": "absolute path of the file to delete (moved to trash by default)"},
        "delete_folder": {"path": "absolute path of the folder to delete (moved to trash by default)"},
        "archive": {"source": "file or folder to zip", "destination": "absolute path of the .zip archive to create"},
        "extract": {"path": "absolute path of the .zip archive", "destination": "(optional) folder to extract into"},
        "touch": {"path": "file to create or update the timestamp of"},
        "bulk_rename": {"path": "folder containing the files", "pattern": "new name pattern, use # for a counter (e.g. photo_###)"},
        "append_file": {"path": "file to append to", "content": "text to append"},
        "send_message": {"to": "WhatsApp chat name or phone number", "message": "text to send"},
        "send_file": {"to": "WhatsApp chat name or phone number", "path": "absolute path of the local file to send"},
        "list_chats": {"limit": "optional maximum number of chats to list (default 50)", "unread_only": "optional boolean to list only unread chats"},
        "get_messages": {"chat": "WhatsApp chat name or id", "limit": "optional number of messages"},
        "get_whatsapp_chat_messages": {"chat": "WhatsApp contact or group name", "limit": "optional number of messages", "days": "optional days window (default 3)"},
        "get_unread_messages": {"chat_limit": "optional maximum chats to check", "messages_per_chat": "optional messages per unread chat"},
        "get_recent_whatsapp_activity": {"chat_limit": "optional maximum active chats to inspect", "messages_per_chat": "optional messages to fetch per active chat", "days": "optional days window (default 3)"},
        "search_messages": {"chat": "WhatsApp chat name or id", "query": "text to search for"},
        "send_report": {"to": "WhatsApp chat name or phone number", "path": "file or folder to summarize and send"},
        "unread_digest": {"to": "optional — chat to send the digest to; omit to just return it"},
        "send_email": {"to": "recipient email address", "subject": "optional email subject (omit for no subject)", "body": "email body text", "attachments": "optional list of absolute file paths to attach to the email"},
        "list_recent_emails": {"query": "optional search query (e.g. from:user subject:hello); omit to list recent inbox mail", "max_results": "optional maximum number of emails to return"},
        "list_drive_files": {"page_size": "optional maximum number of files (default 15)", "folder_id": "optional folder id", "query": "optional Drive query filter"},
        "read_drive_file": {"file_id": "Google Drive file id to read or download", "destination": "optional local file path to save download"},
        "upload_drive_file": {"path": "absolute path of the local file to upload to Drive", "folder_id": "optional Drive destination folder id", "name": "optional name for the file in Drive"},
        "search_drive": {"query": "search keyword or fullText query for Google Drive", "file_type": "optional file type filter (document, spreadsheet, pdf, image, folder)", "max_results": "optional maximum results"},
        "fork": {
            "objective": "Concise high-level description of the primary coding/automation task",
            "requirements": "(optional) List of explicit technical requirements or libraries the worker must fulfill",
            "constraints": "(optional) List of negative boundaries (files/tables/APIs the worker must NOT modify)",
            "success_criteria": "(optional) List of measurable pass/fail completion conditions",
            "fs_scope": "(optional) Target project root directory path (defaults to 'D:/AI-Automation')",
        },
        "shutdown_system": {"delay_seconds": "(optional) seconds before shutdown (default 10)", "force": "(optional) boolean force close", "message": "(optional) comment"},
        "cancel_shutdown": {},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        registry: Optional[ToolRegistry] = None,
        *,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ):
        from app.core.config import settings

        self.base_url = base_url or "https://api.groq.com/openai/v1"
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
        self.model = model or os.getenv("GROQ_MODEL") or settings.GROQ_MODEL
        self.registry = registry
        self.max_tokens = max_tokens
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not set (set it in backend/.env)")
        # If a custom base_url was supplied (e.g. OpenRouter), adjust the
        # auth header accordingly – OpenRouter uses the same Bearer schema.
        self.client = httpx.AsyncClient(
            base_url=self.base_url, timeout=30.0,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )

    # ------------------------------------------------------------------
    # System prompts
    # ------------------------------------------------------------------

    @staticmethod
    def _tools_block() -> str:
        lines = []
        for name, params in OpenCodeAdapter._KNOWN_TOOLS.items():
            param_desc = ", ".join(f"{k} ({desc})" for k, desc in params.items())
            lines.append(f"- {name}: params: {param_desc}")
        return "\n".join(lines)

    def _planning_system_prompt(self) -> str:
        """Prompt that makes the LLM return a structured plan (or direct response)."""
        tools = self._tools_block()
        return (
            "You are Jarvis, an executive AI assistant and orchestrator. You manage WhatsApp, "
            "Gmail, Google Drive, local files, and autonomous development workers (Antigravity). "
            "Analyze the user's request and decide what to do.\n\n"
            f"Available tools and their required params:\n{tools}\n\n"
            "RULES:\n"
            "1. If the prompt is NOT an actionable operation (greeting, question, "
            "conversation), return a direct conversational response.\n"
            "   - If the user asks what tools, features, or capabilities you have, provide a complete, well-structured summary of all 5 integrated modules: (1) Autonomous Worker Delegation ('fork'), (2) Google Drive ('list_drive_files', 'read_drive_file', 'upload_drive_file', 'search_drive'), (3) WhatsApp ('get_unread_messages', 'get_recent_whatsapp_activity', 'get_whatsapp_chat_messages', 'send_message', 'send_file', 'list_chats'), (4) Gmail ('send_email', 'list_recent_emails'), and (5) Local File Management ('list_directory', 'read_file', 'write_file', 'search_files', 'organize_downloads', 'archive', 'extract', etc.).\n"
            "2. If the prompt IS an actionable operation (WhatsApp, email, Google Drive, files), "
            "plan the exact steps needed.\n"
            "   - For checking unread WhatsApp messages: use 'get_unread_messages'.\n"
            "   - For checking active chats / recent WhatsApp activity over the past 3 days (Today, Yesterday, Tuesday): use 'get_recent_whatsapp_activity'.\n"
            "   - For retrieving chat history from a specific contact/group: use 'get_whatsapp_chat_messages' with param 'chat'.\n"
            "2b. If the user asks for a coding, development, testing, refactoring, building, or multi-step engineering task (or explicitly says 'fork', 'delegate', 'spawn worker'):\n"
            "   - Plan a single step with the 'fork' tool.\n"
            "   - In 'objective', provide a clear concise summary of the primary goal.\n"
            "   - In 'requirements', extract a list of specific requirements/libraries/features requested (if any).\n"
            "   - In 'constraints', extract any negative boundaries or things NOT to touch/break (if any).\n"
            "   - In 'success_criteria', extract measurable pass/fail conditions like tests passing (if any).\n"
            "   - In 'fs_scope', specify the target workspace folder path where the worker should execute (use the exact directory if the user mentions one, e.g. 'in frontend', 'in D:/projects/site'; otherwise default to 'D:/workspace').\n"
            "3. Each step maps to exactly ONE of the available tools listed above, using the "
            "exact param names shown.\n"
            "4. Use absolute paths for files (including email/WhatsApp attachments). "
            "Never invent paths, email addresses, or recipients — if required information "
            "is missing from the request, ask for it in a direct response instead of planning.\n"
            "5. Keep steps minimal: only the operations strictly needed to fulfil the request.\n"
            "6. Explain what you are going to do before executing.\n\n"
            "RESPONSE FORMATS:\n\n"
            "For non-actionable prompts (greetings, questions, chitchat, missing information):\n"
            '{"type": "response", "message": "<your conversational reply>"}\n\n'
            "For actionable prompts:\n"
            '{"type": "plan", "reasoning": "<brief explanation of what you will do>", '
            '"steps": [{"tool": "<tool_name>", "params": {<params>}, '
            '"description": "<short human-readable description of this step>"}]}\n\n'
            "Return ONLY the JSON object. No markdown fences, no commentary."
        )

    def _execution_system_prompt(self) -> str:
        """Prompt used for single-step execution (legacy / fallback)."""
        tools = self._tools_block()
        return (
            "You are an assistant that translates natural language commands into a JSON object. "
            "Respond with ONLY the JSON, no markdown fences, no commentary. "
            f"Available tools and their required params:\n{tools}\n\n"
            'Return format: {"tool": "<tool_name>", "params": {"<param>": "<value>"}}. '
            "Use absolute paths wherever a path is required. "
            "If the prompt is not an actionable operation (e.g. greeting, question, conversation), "
            'respond with {"tool": "none", "params": {}}. '
            "Never guess a tool or invent a path."
        )

    # ------------------------------------------------------------------
    # LLM call helpers
    # ------------------------------------------------------------------

    async def _chat(self, messages: List[Dict[str, str]]) -> str:
        """Send a chat-completion request from a full messages array and return content."""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.0,
        }
        if self.max_tokens:
            payload["max_tokens"] = self.max_tokens
        response = await self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return content

    async def _call_llm(self, system_prompt: str, user_content: str) -> str:
        """Send a chat-completion request and return the raw content string."""
        return await self._chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ])

    def _safe_parse(self, raw: str) -> Any:
        """Parse the LLM's raw output as JSON, returning None on failure."""
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze_prompt(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        memories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Phase 1 — Analyze the user's prompt and return a plan or direct response.

        Args:
            prompt: the user's natural-language request.
            history: optional short-term chat history (list of {role, content}).
            memories: optional long-term facts to inject into the system prompt.

        Returns one of:
          {"type": "response", "message": "..."}
          {"type": "plan", "reasoning": "...", "steps": [...], "plan_id": "..."}
        """
        try:
            system_prompt = self._planning_system_prompt()
            if memories:
                facts = "\n".join(f"- {m}" for m in memories)
                system_prompt += (
                    "\n\nLONG-TERM MEMORY (known facts about the user — use these "
                    f"paths/preferences when relevant):\n{facts}"
                )
            try:
                from app.modules.memory.service_memory import get_service_memory_manager
                service_mem = get_service_memory_manager().build_brain_context_prompt()
                system_prompt += f"\n\n{service_mem}"
            except Exception:
                pass

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(history or [])
            messages.append({"role": "user", "content": prompt})
            raw = await self._chat(messages)
            parsed = self._safe_parse(raw)
        except Exception:
            parsed = None

        if parsed and isinstance(parsed, dict) and parsed.get("type") in ("response", "plan"):
            if parsed["type"] == "plan":
                # Validate and enrich steps
                valid_steps, dropped = self._validate_plan_steps(parsed.get("steps", []))
                if not valid_steps:
                    # LLM proposed steps but none survived validation — say exactly
                    # what is missing instead of a generic "not sure" reply.
                    if dropped:
                        asks = "; ".join(
                            f"{d['tool']} needs: {', '.join(d['missing'])}" for d in dropped[:3]
                        )
                        return {"type": "response", "message":
                                f"I'd be happy to do that, but I need a bit more info — {asks}. Could you provide it?"}
                    return {"type": "response", "message": "I'm not sure what you'd like me to do. Could you be more specific?"}
                parsed["steps"] = valid_steps
                parsed["plan_id"] = uuid.uuid4().hex[:12]
            return parsed

        # Fallback: treat entire prompt as a direct response
        return {"type": "response", "message": "I'm not sure what you'd like me to do. Could you be more specific?"}

    async def run_prompt(self, prompt: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Legacy single-step execution (kept for backward compatibility)."""
        try:
            raw = await self._call_llm(self._execution_system_prompt(), prompt)
            parsed = self._safe_parse(raw)
            if parsed and isinstance(parsed, dict) and parsed.get("tool"):
                return parsed
        except Exception:
            pass

        # Fallback to local parser
        lowered = prompt.lower()
        if "list files in" in lowered:
            parts = lowered.split("list files in", 1)[1].strip().split()
            path = parts[0] if parts else "."
            return {"tool": "list_directory", "params": {"path": path}}
        raise RuntimeError(f"Unable to parse prompt via Groq or fallback")

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()

    async def extract_memories(self, prompt: str, outcome: str, max_facts: int = 3) -> List[str]:
        """Extract durable facts worth remembering from an agent turn.

        Returns a list of fact strings (possibly empty). Never raises — memory
        extraction is best-effort and must not break the main flow.
        """
        system_prompt = (
            "You are a memory extractor for a file-assistant agent. "
            "Decide which facts from this conversation are worth remembering LONG-TERM "
            "(user preferences, important folders/paths, recurring workflows, habits). "
            "Do NOT store one-off request details, file contents, or temporary state. "
            f"Return at most {max_facts} facts as a JSON object: "
            '{"facts": ["fact 1", "fact 2"]}. If nothing is worth remembering, '
            'return {"facts": []}. Return ONLY the JSON object.'
        )
        user_content = f"User said: {prompt}\nWhat happened: {outcome}"
        try:
            raw = await self._call_llm(system_prompt, user_content)
            parsed = self._safe_parse(raw)
        except Exception:
            return []
        if not isinstance(parsed, dict):
            return []
        facts = parsed.get("facts", [])
        if not isinstance(facts, list):
            return []
        return [str(f).strip()[:300] for f in facts if str(f).strip()][:max_facts]

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _validate_plan_steps(self, steps: Any) -> tuple:
        """Filter the LLM's plan steps to only those using known tools.

        A step is kept only if:
          - the tool is in ``_KNOWN_TOOLS``, and
          - all params required by the tool's ``input_schema`` are present
            and non-empty.

        Returns (valid_steps, dropped) where dropped is a list of
        {"tool", "reason", "missing"} dicts explaining rejected steps so the
        caller can ask the user for exactly what's missing.
        """
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

    def _required_params(self, tool_name: str) -> List[str]:
        """Return the required params for a tool from its registered input schema."""
        if self.registry is not None:
            try:
                tool = self.registry.get(tool_name)
                return list(tool.input_schema.get("required", []))
            except KeyError:
                pass
        # Fallback: every documented param is required except known optionals
        optional = {"target_dir", "recursive", "dry_run", "destination", "case_sensitive",
                    "max_results", "permanent", "extension", "start_index",
                    "page_size", "folder_id", "query", "order_by", "file_type", "max_bytes", "name",
                    # fork pseudo-tool: everything falls back to context if omitted
                    "objective", "fs_scope", "allowed_tools", "worker_type", "max_steps",
                    "requirements", "constraints", "success_criteria"}
        return [k for k in self._KNOWN_TOOLS[tool_name] if k not in optional]
