import asyncio
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, Set

from app.core.execution_engine import ExecutionEngine
from app.registry.tool_registry import ToolRegistry
from app.workers.base.bus import EventBus, emit
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
        self._plan_approved_event = asyncio.Event()
        self._awaiting_plan_approval = False
        self._implementation_plan: Optional[str] = None
        self._test_results: Dict[str, Any] = {}

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
                "plan_status": "pending",
                "implementation_plan": None,
                "test_results": {},
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
                "plan_status": self._contract.plan_status,
            }
        
        status = "cancelled" if self._cancelled else (
            "awaiting_plan_approval" if self._awaiting_plan_approval else (
                "running" if running else "completed"
            )
        )

        return {
            "status": status,
            "progress_percent": state.get("progress_percent", 0),
            "current_step": state.get("current_step"),
            "completed": state.get("completed", []),
            "remaining": state.get("remaining", []),
            "errors": state.get("errors", []),
            "implementation_plan": self._implementation_plan or self._session.read_plan(),
            "test_results": self._test_results or self._session.read_test_results(),
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

    def approve_plan(self, approved_plan: Optional[str] = None) -> bool:
        """Approve the implementation plan and resume worker execution."""
        if approved_plan:
            self._implementation_plan = approved_plan
            if self._contract:
                self._contract.implementation_plan = approved_plan
            if self._session:
                self._session.write_plan(approved_plan)

        if self._contract:
            self._contract.plan_status = "approved"

        if self._session:
            self._session.append_event("PLAN_APPROVED", {"plan": self._implementation_plan or ""})
            self._session.write_state({
                "status": "running",
                "current_step": "Job 2: Execute Implementation Plan",
                "plan_status": "approved",
                "implementation_plan": self._implementation_plan or self._session.read_plan(),
            })

        emit(self._session_id, "PLAN_APPROVED", {"plan": self._implementation_plan or ""})
        self._awaiting_plan_approval = False
        self._plan_approved_event.set()
        return True

    def reject_plan(self, feedback: str) -> bool:
        """Reject or request changes to the implementation plan with feedback."""
        if self._contract:
            self._contract.plan_status = "rejected"

        if self._session:
            self._session.append_event("PLAN_REJECTED", {"feedback": feedback})
            self._session.write_state({
                "status": "running",
                "current_step": "Revising Implementation Plan",
                "plan_status": "rejected",
                "implementation_plan": self._implementation_plan or self._session.read_plan(),
            })

        emit(self._session_id, "PLAN_REJECTED", {"feedback": feedback})
        self.intervene(f"Plan revision request: {feedback}")
        self._awaiting_plan_approval = False
        self._plan_approved_event.set()
        return True

    def cancel(self) -> None:
        """Request cooperative cancellation of the worker loop."""
        self._cancelled = True
        self._plan_approved_event.set()
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
            if hasattr(agent, "requires_plan_approval"):
                agent.requires_plan_approval = contract.requires_plan_approval
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

                # Handle Plan Ready & Review Gate
                if action == "plan_ready":
                    plan_text = decision.get("plan") or ""
                    self._implementation_plan = plan_text
                    self._session.write_plan(plan_text)
                    if self._contract:
                        self._contract.implementation_plan = plan_text
                        self._contract.plan_status = "awaiting_approval"

                    step_name = decision.get("params", {}).get("step", "Job 1: Author Implementation Plan")
                    completed.append(step_name)
                    ev.step_completed(step_name, step_index, output={"plan": plan_text[:500]})
                    self._session.append_event("PLAN_READY", {"step": step_name, "plan": plan_text})

                    if contract.requires_plan_approval:
                        self._awaiting_plan_approval = True
                        self._plan_approved_event.clear()
                        self._session.write_state({
                            "status": "awaiting_plan_approval",
                            "current_step": "Awaiting Plan Approval",
                            "completed": completed,
                            "remaining": [contract.objective],
                            "errors": [e["message"] for e in errors],
                            "progress_percent": 33,
                            "plan_status": "awaiting_approval",
                            "implementation_plan": plan_text,
                        })
                        logger.info("Worker session %s is awaiting plan approval", self._session_id)
                        await self._plan_approved_event.wait()

                        if self._cancelled:
                            break

                        if hasattr(agent, "set_approved_plan"):
                            agent.set_approved_plan(self._implementation_plan or "")

                        # Immediately update disk state so pollers and SSE clients see running state while Job 2 executes
                        self._session.write_state({
                            "status": "running",
                            "current_step": "Job 2: Execute Implementation Plan",
                            "completed": completed,
                            "remaining": [contract.objective],
                            "errors": [e["message"] for e in errors],
                            "progress_percent": 35,
                            "plan_status": self._contract.plan_status if self._contract else "approved",
                            "implementation_plan": self._implementation_plan or self._session.read_plan(),
                            "test_results": self._test_results or self._session.read_test_results(),
                        })

                    continue

                # action == "tool"
                step_index += 1
                tool_name = decision["tool"]
                params = decision.get("params", {})
                step_name = params.get("step") or tool_name

                # Capture test results if this was the testing phase
                if tool_name == "self_testing" or "test_results" in params:
                    test_data = params.get("test_results") or {}
                    self._test_results = test_data
                    self._session.write_test_results(test_data)
                    if self._contract:
                        self._contract.test_results = test_data

                # Update live state
                self._session.write_state({
                    "status": "running",
                    "current_step": step_name,
                    "completed": completed,
                    "remaining": [contract.objective] if not completed else [],
                    "errors": [e["message"] for e in errors],
                    "progress_percent": int(step_index / max(max_steps, 1) * 100),
                    "plan_status": self._contract.plan_status if self._contract else "approved",
                    "implementation_plan": self._implementation_plan or self._session.read_plan(),
                    "test_results": self._test_results or self._session.read_test_results(),
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

        artifacts = self._collect_artifacts(agent)
        result_data = {
            "success": success,
            "completed_steps": len(completed),
            "tools_used": completed,
            "errors": errors,
            "cancelled": self._cancelled,
            "summary": summary,
            "implementation_plan": self._implementation_plan or self._session.read_plan(),
            "test_results": self._test_results or self._session.read_test_results(),
            "artifacts": artifacts,
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
        artifacts = self._collect_artifacts(None)
        result_data = {
            "success": success,
            "completed_steps": len(completed),
            "tools_used": completed,
            "errors": errors,
            "cancelled": self._cancelled,
            "artifacts": artifacts,
        }
        self._finalize(ev, completed, errors, result_data)
        return result_data

    def _collect_artifacts(self, agent: Any = None) -> List[str]:
        """Discover and collect absolute paths of generated files/artifacts in priority order."""
        from pathlib import Path
        import json
        import re

        artifacts: List[str] = []
        seen = set()

        def _is_test_script(p: Path) -> bool:
            name_lower = p.name.lower()
            return (
                name_lower.startswith(("test_", "verify_", "conftest"))
                or name_lower.endswith(("_test.py", "test.py"))
                or name_lower in ("implementation_plan.md", "task.json", "state.json", "result.json", "test_results.json")
            )

        def _add(path_str: Any, is_priority: bool = False):
            if not path_str or not isinstance(path_str, str):
                return
            cleaned = path_str.strip().strip("'\"")
            if not cleaned:
                return
            if cleaned.startswith("file:///"):
                cleaned = cleaned.replace("file:///", "")
            elif cleaned.startswith("file://"):
                cleaned = cleaned.replace("file://", "")
            p = Path(cleaned)
            try:
                if p.is_file() and str(p.resolve()) not in seen:
                    # Ignore internal logs/state json files and test scripts
                    if not p.name.endswith((".json", ".jsonl", ".log", ".tmp")) and not _is_test_script(p):
                        resolved = str(p.resolve())
                        seen.add(resolved)
                        if is_priority:
                            artifacts.insert(0, resolved)
                        else:
                            artifacts.append(resolved)
            except Exception:
                pass

        scope_dir = Path(self._contract.fs_scope) if self._contract and self._contract.fs_scope else Path(".")

        # 1. High Priority: Files explicitly mentioned in the contract objective or requirements
        text_priority_sources = []
        if self._contract:
            if self._contract.objective:
                text_priority_sources.append(self._contract.objective)
            if self._contract.requirements:
                text_priority_sources.extend(self._contract.requirements)
            if self._contract.success_criteria:
                text_priority_sources.extend(self._contract.success_criteria)

        for txt in text_priority_sources:
            if not txt:
                continue
            win_matches = re.findall(r"([A-Za-z]:(?:\\\\|/|\\)[\w\-\.\s\\/]+\.[a-zA-Z0-9]{1,8})", txt)
            for wm in win_matches:
                _add(wm.replace("\\\\", "\\"), is_priority=True)
            rel_matches = re.findall(r"['\"]?([\w\-\.]+\.[a-zA-Z0-9]{1,8})['\"]?", txt)
            for rm in rel_matches:
                cand = scope_dir / rm
                if cand.is_file():
                    _add(str(cand), is_priority=True)

        # 2. Inspect session.path / "artifacts"
        try:
            if self._session and self._session.path:
                art_dir = self._session.path / "artifacts"
                if art_dir.is_dir():
                    for f in sorted(art_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                        if f.is_file():
                            _add(str(f), is_priority=True)
        except Exception:
            pass

        # 3. Target Files table from Implementation Plan
        if agent and hasattr(agent, "implementation_plan") and agent.implementation_plan:
            win_matches = re.findall(r"([A-Za-z]:(?:\\\\|/|\\)[\w\-\.\s\\/]+\.[a-zA-Z0-9]{1,8})", agent.implementation_plan)
            for wm in win_matches:
                _add(wm.replace("\\\\", "\\"), is_priority=True)

        # 4. Extract paths mentioned in agent's execution summary
        if agent and hasattr(agent, "_execution_summary") and agent._execution_summary:
            win_matches = re.findall(r"([A-Za-z]:(?:\\\\|/|\\)[\w\-\.\s\\/]+\.[a-zA-Z0-9]{1,8})", agent._execution_summary)
            for wm in win_matches:
                _add(wm.replace("\\\\", "\\"), is_priority=True)
            rel_matches = re.findall(r"(?:created|written|saved|file|path|to)\s+['\"]?([\w\-\.]+\.[a-zA-Z0-9]{1,8})['\"]?", agent._execution_summary, re.IGNORECASE)
            for rm in rel_matches:
                _add(str(scope_dir / rm), is_priority=True)

        # 5. Inspect fs_scope directory for recently created/modified non-test files
        try:
            if scope_dir.is_dir():
                for f in sorted(scope_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                    if f.is_file():
                        _add(str(f))
        except Exception:
            pass

        return artifacts

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
        if tool_name in ("task_execution", "apply_intervention", "opencode_milestone", "self_testing"):
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
        final_status = "cancelled" if self._cancelled else ("completed" if result_data.get("success") else "failed")
        self._session.write_state({
            "status": final_status,
            "current_step": None,
            "completed": completed,
            "remaining": [],
            "errors": [e["message"] for e in errors],
            "progress_percent": 100 if not self._cancelled else self._session.progress_percent,
        })
        try:
            handover = self._synthesize_handover(result_data)
            result_data["handover"] = handover
        except Exception as exc:
            logger.warning("Could not synthesize session handover: %s", exc)
        self._session.write_result(result_data)
        self._session.append_event("WORK_COMPLETED", result_data)
        ev.work_completed(result_data)

    def _synthesize_handover(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize a compact session handover brief and folder manifests."""
        import datetime
        from pathlib import Path
        import json

        scope_dir = Path(self._contract.fs_scope) if self._contract else Path(".")
        manifests: List[str] = []
        try:
            if scope_dir.is_dir():
                for p in scope_dir.rglob("README.md"):
                    if p.is_file():
                        try:
                            rel_p = str(p.relative_to(scope_dir))
                            manifests.append(rel_p)
                        except Exception:
                            manifests.append(str(p))
        except Exception:
            pass

        artifacts = result_data.get("artifacts") or []
        summary = result_data.get("summary") or ""
        test_res = result_data.get("test_results") or {}
        plan_txt = result_data.get("implementation_plan") or ""

        # Extract architectural decisions or key items from plan/summary
        decisions: List[str] = []
        if plan_txt:
            for line in plan_txt.splitlines():
                line_str = line.strip()
                if line_str.startswith(("-", "*", "•")) and len(line_str) > 10:
                    decisions.append(line_str.lstrip("-*• "))
                if len(decisions) >= 5:
                    break

        # Automatically execute graphify AST extraction if graphify CLI is available
        has_graphify = False
        try:
            if scope_dir.is_dir():
                import shutil
                import subprocess
                if shutil.which("graphify"):
                    cmd = (
                        ["graphify", "update", "."]
                        if (scope_dir / "graphify-out" / "graph.json").is_file()
                        else ["graphify", "extract", ".", "--code-only", "--no-viz"]
                    )
                    subprocess.run(cmd, cwd=str(scope_dir), capture_output=True, timeout=20, check=False)
                    has_graphify = (scope_dir / "graphify-out" / "graph.json").is_file()
        except Exception as exc:
            logger.debug("Automatic graphify execution failed: %s", exc)

        handover = {
            "session_id": self._session_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "objective": self._contract.objective if self._contract else "",
            "status": "completed" if result_data.get("success") else "failed",
            "artifacts": artifacts,
            "folder_manifests": manifests,
            "architecture_decisions": decisions,
            "test_summary": test_res,
            "summary": summary,
            "has_graphify": has_graphify,
        }

        # Format human-readable markdown
        md_lines = [
            "# 📋 Project Handover Brief",
            f"**Session ID**: `{self._session_id}` | **Date**: `{handover['timestamp']}`  ",
            f"**Goal**: {handover['objective']}  ",
            f"**Status**: {handover['status'].upper()}",
            "",
            "## 📁 Key Files & Artifacts",
        ]
        if artifacts:
            for a in artifacts:
                md_lines.append(f"- `{Path(a).name}` (`{a}`)")
        else:
            md_lines.append("- None generated")

        md_lines.extend(["", "## 📂 Folder-Level Documentation"])
        if manifests:
            for m in manifests:
                md_lines.append(f"- `{m}`")
        else:
            md_lines.append("- No subfolder README.md files detected")

        if decisions:
            md_lines.extend(["", "## ⚙️ Architecture & Decisions"])
            for d in decisions:
                md_lines.append(f"- {d}")

        if has_graphify:
            md_lines.extend([
                "",
                "## 🕸️ Knowledge Graph & Architecture (graphify)",
                "AST architecture graph is generated and queryable at `graphify-out/`.",
                "- Query symbols & dependencies: `graphify query \"<question>\"`",
                "- Trace component paths: `graphify path \"<file_a>\" \"<file_b>\"`",
                "- View architecture summary: `graphify-out/GRAPH_REPORT.md`",
            ])

        if test_res:
            md_lines.extend(["", "## 🧪 Verification & Test Results", f"```json\n{json.dumps(test_res, indent=2)}\n```"])

        if summary:
            md_lines.extend(["", "## 📝 Execution Summary", summary])

        handover_md = "\n".join(md_lines) + "\n"

        # Write to session dir
        try:
            self._session.write_handover(handover)
            (self._session.path / "SESSION_HANDOVER.md").write_text(handover_md, encoding="utf-8")
        except Exception as exc:
            logger.debug("Failed writing handover to session dir: %s", exc)

        # Write to workspace scope dir
        try:
            if scope_dir.is_dir():
                (scope_dir / "handover.json").write_text(json.dumps(handover, indent=2), encoding="utf-8")
                (scope_dir / "SESSION_HANDOVER.md").write_text(handover_md, encoding="utf-8")
        except Exception as exc:
            logger.debug("Failed writing handover to scope_dir: %s", exc)

        return handover

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