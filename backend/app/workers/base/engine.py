import asyncio
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, Set

from app.core.execution_engine import ExecutionEngine
from app.registry.tool_registry import ToolRegistry
from app.workers.base.bus import EventBus
from app.workers.base.contract import TaskContract
from app.workers.base.scoped_registry import ScopedToolRegistry
from app.workers.base.session import WorkerSession

logger = logging.getLogger("jarvis.worker.engine")

# An agent is any object exposing:
#   available: bool
#   async decide_next_step() -> {"action": "tool"|"done"|"fail", ...}
#   record_step(tool, success, output=None, error=None)
#   inject_intervention(message)
AgentFactory = Callable[[TaskContract], Any]


class WorkerEngine:
    """Orchestrates a single worker session.

    Lifecycle: fork (create on‑disk session) → run (background worker loop) →
    collect result. The parent can intervene() or cancel() while it runs.

    If an ``agent_factory`` is supplied and the produced agent is available,
    the loop is LLM‑driven (agent decides each step). Otherwise a
    deterministic placeholder loop exercises the plumbing without an LLM key.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        session_id: Optional[str] = None,
        agent_factory: Optional[AgentFactory] = None,
    ):
        self._registry = registry
        self._session_id = session_id or f"ws_{uuid.uuid4().hex[:12]}"
        self._session: Optional[WorkerSession] = None
        self._contract: Optional[TaskContract] = None
        self._agent_factory = agent_factory
        self._loop_task: Optional[asyncio.Task] = None
        self._cancelled = False
        self._interventions: List[str] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def session_id(self) -> str:
        return self._session_id

    def fork(self, contract: TaskContract) -> WorkerSession:
        """Create the on‑disk worker session from a contract."""
        self._contract = contract
        self._session = WorkerSession(self._session_id, contract)
        self._session.fork()
        return self._session

    # ------------------------------------------------------------------
    # State / result accessors (used by REST polling)
    # ------------------------------------------------------------------
    def get_state(self) -> Dict[str, Any]:
        if self._session is None:
            return {
                "status": "idle",
                "progress_percent": 0,
                "current_step": None,
                "completed": [],
                "remaining": [],
                "errors": [],
                "objective": None,
                "fs_scope": None,
                "allowed_tools": [],
            }
        state = self._session.read_state()
        running = self._loop_task is not None and not self._loop_task.done()
        contract_info: Dict[str, Any] = {}
        if self._contract:
            contract_info = {
                "objective": self._contract.objective,
                "fs_scope": self._contract.fs_scope,
                "allowed_tools": self._contract.allowed_tools,
                "max_steps": self._contract.max_steps,
            }
        return {
            "status": "cancelled" if self._cancelled else ("running" if running else "completed"),
            "progress_percent": state.get("progress_percent", 0),
            "current_step": state.get("current_step"),
            "completed": state.get("completed", []),
            "remaining": state.get("remaining", []),
            "errors": state.get("errors", []),
            **contract_info,
        }

    def get_result(self) -> Dict[str, Any]:
        if self._session is None:
            return {}
        result = self._session.read_result()
        # If the loop was cancelled before it could run (race at fork time)
        # no result.json is written — synthesize one from engine state.
        if not result and self._cancelled:
            state = self._session.read_state()
            return {
                "success": False,
                "completed_steps": len(state.get("completed", [])),
                "tools_used": state.get("completed", []),
                "errors": [],
                "cancelled": True,
            }
        return result

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------
    def intervene(self, message: str) -> None:
        """Queue a parent guidance message for the worker loop."""
        self._interventions.append(message)

    def cancel(self) -> None:
        """Request cooperative cancellation of the worker loop."""
        self._cancelled = True
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    async def run(self, contract: TaskContract) -> Dict[str, Any]:
        """Fork the session and start the worker loop as a background task."""
        self.fork(contract)
        self._loop_task = asyncio.create_task(self._worker_loop())
        return self.get_state()

    async def _worker_loop(self) -> Dict[str, Any]:
        assert self._session is not None and self._contract is not None
        contract = self._contract

        agent = self._agent_factory(contract) if self._agent_factory else None
        if agent is not None and getattr(agent, "available", False):
            return await self._agent_loop(agent, contract)
        return await self._placeholder_loop(contract)

    # ==================================================================
    # LLM‑driven loop (Step 1+)
    # ==================================================================
    async def _agent_loop(self, agent: Any, contract: TaskContract) -> Dict[str, Any]:
        ev = EventBus(self._session_id)
        allowed: List[str] = list(dict.fromkeys(contract.allowed_tools))
        scoped = ScopedToolRegistry(self._registry, set(allowed))
        engine = ExecutionEngine(scoped)
        max_steps = contract.max_steps

        ev.work_started({"objective": contract.objective, "tools": allowed, "mode": "agent"})
        self._session.append_event(
            "WORK_STARTED", {"objective": contract.objective, "tools": allowed, "mode": "agent"}
        )

        completed: List[str] = []
        errors: List[Dict[str, str]] = []
        summary = ""
        consecutive_failures = 0
        step_index = 0
        action = None

        try:
            while step_index < max_steps and not self._cancelled:
                self._drain_interventions(agent)

                decision = await agent.decide_next_step()
                action = decision.get("action")

                if action == "fail":
                    reason = decision.get("reason", "unknown")
                    logger.warning("Worker agent decision failed: %s", reason)
                    errors.append({"tool": "agent", "message": reason})
                    ev.validation_failed("agent_decision", [reason])
                    break

                if action == "done":
                    summary = decision.get("summary", "")
                    break

                # action == "tool"
                step_index += 1
                tool_name = decision["tool"]
                params = decision.get("params", {})
                ok, out_data, err_msg = await self._execute_step(
                    ev, engine, tool_name, params, step_index - 1, completed, errors, total=max_steps
                )
                agent.record_step(
                    tool_name,
                    ok,
                    output=out_data if ok else None,
                    error=err_msg if not ok else None,
                )
                consecutive_failures = 0 if ok else consecutive_failures + 1
                if consecutive_failures >= 3:
                    logger.warning("Worker stopped: 3 consecutive tool failures")
                    errors.append({"tool": tool_name, "message": "Stopped after 3 consecutive failures"})
                    break
        except asyncio.CancelledError:
            self._cancelled = True

        self._drain_interventions(agent, to_events_only=True)

        if self._cancelled:
            success = False
        elif action == "done":
            success = True
        else:
            success = bool(completed) and not errors

        result_data = {
            "success": success,
            "completed_steps": len(completed),
            "tools_used": completed,
            "errors": errors,
            "cancelled": self._cancelled,
            "summary": summary,
        }
        self._finalize(ev, completed, errors, result_data)
        return result_data

    # ==================================================================
    # Deterministic placeholder loop (Step 0 — no LLM key needed)
    # ==================================================================
    async def _placeholder_loop(self, contract: TaskContract) -> Dict[str, Any]:
        ev = EventBus(self._session_id)
        allowed: List[str] = list(dict.fromkeys(contract.allowed_tools))
        scoped = ScopedToolRegistry(self._registry, set(allowed))
        engine = ExecutionEngine(scoped)
        max_steps = contract.max_steps

        ev.work_started({"objective": contract.objective, "tools": allowed, "mode": "placeholder"})
        self._session.append_event(
            "WORK_STARTED", {"objective": contract.objective, "tools": allowed, "mode": "placeholder"}
        )

        completed: List[str] = []
        errors: List[Dict[str, str]] = []
        total = max(len(allowed), 1)

        try:
            for idx, tool_name in enumerate(allowed[:max_steps]):
                if self._cancelled:
                    break
                params = self._placeholder_params(tool_name)
                await self._execute_step(
                    ev, engine, tool_name, params, idx, completed, errors, total=total
                )
        except asyncio.CancelledError:
            self._cancelled = True

        self._drain_interventions(None, to_events_only=True)

        success = not self._cancelled and bool(completed) and not errors
        result_data = {
            "success": success,
            "completed_steps": len(completed),
            "tools_used": completed,
            "errors": errors,
            "cancelled": self._cancelled,
        }
        self._finalize(ev, completed, errors, result_data)
        return result_data

    # ==================================================================
    # Shared helpers
    # ==================================================================
    async def _execute_step(
        self,
        ev: EventBus,
        engine: ExecutionEngine,
        tool_name: str,
        params: Dict[str, Any],
        idx: int,
        completed: List[str],
        errors: List[Dict[str, str]],
        total: int,
    ) -> tuple[bool, Any, Optional[str]]:
        """Run one tool step: update state, emit events, record outcome.

        Returns (ok, output_data, error_message). Mutates ``completed`` / ``errors`` in place.
        """
        ev.step_started(tool_name, idx)
        self._session.write_state({
            "current_step": tool_name,
            "completed": completed,
            "remaining": [],
            "errors": [e["message"] for e in errors],
            "progress_percent": int(len(completed) / max(total, 1) * 100),
        })

        # Internal milestone step (already executed by OpenCode worker agent)
        if tool_name == "opencode_milestone":
            phase = params.get("phase", "milestone")
            step_label = f"milestone_{phase}"
            error_msg = params.get("error")
            if error_msg:
                errors.append({"tool": step_label, "message": error_msg})
                ev.step_completed(step_label, idx, output={}, errors=[error_msg])
                self._session.append_event(
                    "STEP_FAILED", {"step": step_label, "index": idx, "error": error_msg, "params": params}
                )
                return False, None, error_msg

            completed.append(step_label)
            output_data = params
            ev.step_completed(step_label, idx, output=output_data)
            self._session.append_event(
                "STEP_COMPLETED", {"step": step_label, "index": idx, "output": output_data}
            )
            return True, output_data, None

        try:
            result = await engine.run(tool_name, params)
        except Exception as exc:
            message = str(exc)
            errors.append({"tool": tool_name, "message": message})
            ev.step_completed(tool_name, idx, output={}, errors=[message])
            self._session.append_event("STEP_FAILED", {"step": tool_name, "index": idx, "error": message})
            return False, None, message

        if result.success:
            completed.append(tool_name)
            output_data = result.data or {}
            ev.step_completed(tool_name, idx, output=output_data)
            self._session.append_event(
                "STEP_COMPLETED", {"step": tool_name, "index": idx, "output": output_data}
            )
            return True, output_data, None

        message = (result.error or {}).get("message", "unknown error")
        errors.append({"tool": tool_name, "message": message})
        ev.step_completed(tool_name, idx, output={}, errors=[message])
        self._session.append_event(
            "STEP_FAILED", {"step": tool_name, "index": idx, "error": message}
        )
        return False, None, message

    def _drain_interventions(self, agent: Any = None, to_events_only: bool = False) -> None:
        """Pass queued parent messages to the agent (and/or the event log)."""
        while self._interventions:
            msg = self._interventions.pop(0)
            self._session.append_event("PARENT_INTERVENTION", {"message": msg})
            if agent is not None and not to_events_only:
                agent.inject_intervention(msg)

    def _finalize(
        self,
        ev: EventBus,
        completed: List[str],
        errors: List[Dict[str, str]],
        result_data: Dict[str, Any],
    ) -> None:
        self._session.write_state({
            "current_step": None,
            "completed": completed,
            "remaining": [],
            "errors": [e["message"] for e in errors],
            "progress_percent": 100 if not self._cancelled else self._session.progress_percent,
        })
        self._session.write_result(result_data)
        self._session.append_event("WORK_COMPLETED", result_data)
        ev.work_completed(result_data)

    # ==================================================================
    # Step‑0 placeholder parameter map — replaced by LLM decisions when
    # the agent is available
    # ==================================================================
    @staticmethod
    def _placeholder_params(tool_name: str) -> Dict[str, Any]:
        base = str(WorkerSession.SESSIONS_ROOT)
        table: Dict[str, Dict[str, Any]] = {
            "list_directory": {"path": base},
            "exists": {"path": base},
            "read_file": {"path": str(WorkerSession.SESSIONS_ROOT.parent / "README.md")},
            "create_file": {"path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "worker_created.txt")},
            "write_file": {"path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "worker_output.txt"), "content": "worker output"},
            "create_folder": {"path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "newfolder")},
            "touch": {"path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "touched.txt")},
            "append_file": {"path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "worker_output.txt"), "content": "\nappended"},
            "metadata": {"path": base},
            "search_files": {"path": base, "pattern": "*.json"},
            "search_content": {"path": base, "query": "objective"},
            "copy": {
                "source": str(WorkerSession.SESSIONS_ROOT / "task.json"),
                "destination": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "task_copy.json"),
            },
            "move": {
                "source": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "worker_created.txt"),
                "destination": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "worker_moved.txt"),
            },
            "rename": {
                "source": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "worker_moved.txt"),
                "destination": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "worker_renamed.txt"),
            },
            "archive": {
                "source": str(WorkerSession.SESSIONS_ROOT / "artifacts"),
                "destination": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "artifacts.zip"),
            },
            "extract": {
                "path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "artifacts.zip"),
                "destination": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "extracted"),
            },
            "bulk_rename": {"path": str(WorkerSession.SESSIONS_ROOT / "artifacts"), "pattern": "file_##"},
            "delete_file": {"path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "worker_renamed.txt")},
            "delete_folder": {"path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "extracted")},
            "organize_downloads": {
                "source_dir": str(WorkerSession.SESSIONS_ROOT / "artifacts"),
                "target_dir": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "organized"),
            },
            # Document worker tools — placeholder runs them against a fixture
            "create_docx": {
                "path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "created.docx"),
                "title": "New Document",
                "initial_text": "Sample text",
                "overwrite": True,
            },
            "add_heading": {
                "path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "sample.docx"),
                "text": "New Heading",
                "level": 1,
            },
            "add_paragraph": {
                "path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "sample.docx"),
                "text": "Appended paragraph text",
            },
            "add_table": {
                "path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "sample.docx"),
                "headers": ["Col 1", "Col 2"],
                "rows": [["A", "B"]],
            },
            "inspect_docx": {"path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "sample.docx")},
            "read_docx": {"path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "sample.docx")},
            "normalize_headings": {"path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "sample.docx")},
            "fix_spacing": {"path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "sample.docx")},
            "format_tables": {"path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "sample.docx")},
            "backup_docx": {"path": str(WorkerSession.SESSIONS_ROOT / "artifacts" / "sample.docx")},
        }
        return table.get(tool_name, {})