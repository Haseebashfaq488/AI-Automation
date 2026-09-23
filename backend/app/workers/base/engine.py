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
from app.workers.base.guardian import ActiveStreamGuardian

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
        self._guardian: Optional[ActiveStreamGuardian] = None
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
        contract.task_id = contract.task_id or self._session_id
        self._contract = contract
        self._session = WorkerSession(self._session_id, contract)
        self._session.fork()
        self._guardian = ActiveStreamGuardian(contract, self._session_id)
        return self._session

    def get_guardian_status(self) -> Dict[str, Any]:
        """Return real-time supervision status from the stream guardian."""
        if self._guardian:
            return self._guardian.get_status()
        return {}

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
        await asyncio.sleep(0)
        return self.get_state()

    async def _worker_loop(self) -> Dict[str, Any]:
        assert self._session is not None and self._contract is not None
        contract = self._contract

        agent = self._agent_factory(contract) if self._agent_factory else None
        if agent is not None:
            if hasattr(agent, "worker_session_id") and not getattr(agent, "worker_session_id", None):
                agent.worker_session_id = self._session_id
            binary_check = None
            try:
                from app.workers.antigravity_worker.agent import config as agy_config
                binary_check = agy_config.get_agy_binary()
            except Exception:
                pass
            if binary_check is None:
                agent.available = False

        if agent is not None and getattr(agent, "available", False):
            return await self._agent_loop(agent, contract)
        return await self._placeholder_loop(contract)

    # ==================================================================
    # LLM‑driven loop (Direct Task Execution & Streaming)
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
                step_name = params.get("step") or tool_name

                # Update live state
                self._session.write_state({
                    "status": "running",
                    "current_step": step_name,
                    "completed": completed,
                    "remaining": [contract.objective] if not completed else [],
                    "errors": [e["message"] for e in errors],
                    "progress_percent": int(step_index / max(max_steps, 1) * 100),
                })
                ev.step_started(step_name, step_index - 1)
                self._session.append_event(
                    "STEP_STARTED", {"step": step_name, "index": step_index - 1, "tool": tool_name}
                )

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
    # Deterministic placeholder loop (No LLM key needed)
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
                await asyncio.sleep(0)
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
        """Run one tool step: update state, emit events, record outcome."""
        step_label = params.get("step") or tool_name

        self._session.write_state({
            "current_step": step_label,
            "completed": completed,
            "remaining": [],
            "errors": [e["message"] for e in errors],
            "progress_percent": int(len(completed) / max(total, 1) * 100),
        })

        # Direct autonomous task execution or intervention (executed by CLI driver)
        if tool_name in ("task_execution", "apply_intervention", "opencode_milestone"):
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
            errors.append({"tool": step_label, "message": message})
            ev.step_completed(step_label, idx, output={}, errors=[message])
            self._session.append_event("STEP_FAILED", {"step": step_label, "index": idx, "error": message})
            return False, None, message

        if result.success:
            completed.append(step_label)
            output_data = result.data or {}
            ev.step_completed(step_label, idx, output=output_data)
            self._session.append_event(
                "STEP_COMPLETED", {"step": step_label, "index": idx, "output": output_data}
            )
            return True, output_data, None

        # Inspect events via guardian
        if self._guardian:
            guardian_intervention = self._guardian.inspect_event(
                "STEP_COMPLETED" if result.success else "STEP_FAILED",
                {"tool": tool_name, "params": params, "output": result.data if result.success else None, "error": str(result.error) if not result.success else None, "success": result.success}
            )
            if guardian_intervention:
                self.intervene(guardian_intervention)

        message = (result.error or {}).get("message", "unknown error")
        errors.append({"tool": step_label, "message": message})
        ev.step_completed(step_label, idx, output={}, errors=[message])
        self._session.append_event(
            "STEP_FAILED", {"step": step_label, "index": idx, "error": message}
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

    def _placeholder_params(self, tool_name: str) -> Dict[str, Any]:
        scope = self._contract.fs_scope if self._contract else "."
        import os
        sample_path = os.path.join(scope, "worker_test_file.txt")
        if tool_name in ("create_file", "touch"):
            return {"path": sample_path, "content": "placeholder content"}
        if tool_name == "write_file":
            return {"path": sample_path, "content": "updated content"}
        if tool_name in ("exists", "metadata", "read_file"):
            return {"path": sample_path}
        if tool_name == "list_directory":
            return {"path": scope}
        return {}