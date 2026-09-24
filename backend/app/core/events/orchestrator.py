import asyncio
import logging
import threading
from typing import Any, Dict, List, Optional

from app.core.events.bus import get_event_bus
from app.core.events.schema import EventType, JarvisEvent, ReactiveHook
from app.registry import registry

logger = logging.getLogger("jarvis.events.orchestrator")


class TaskOrchestrator:
    """Reactive Event-Driven Task Orchestrator.

    Allows Jarvis to chain dependent tasks asynchronously:
    E.g. "Create a file -> When worker finishes, automatically send file via WhatsApp".
    """

    def __init__(self):
        self._hooks: Dict[str, List[ReactiveHook]] = {}
        self._hooks_lock = threading.Lock()
        self._listening = False

    def start(self) -> None:
        """Attach listener to the global event bus."""
        if self._listening:
            return
        bus = get_event_bus()
        bus.on(EventType.WORKER_COMPLETED, self._on_worker_completed)
        bus.on(EventType.WORKER_FAILED, self._on_worker_failed)
        self._listening = True
        logger.info("TaskOrchestrator initialized and listening for worker completion & failure events.")

    def check_and_execute_pending_if_completed(self, session_id: str) -> None:
        """Self-healing check: if worker is already finished on disk, trigger pending hooks."""
        from app.workers.base.session import WorkerSession
        try:
            session = WorkerSession(session_id)
            if (session.path / "result.json").is_file():
                result_data = session.read_result()
                if result_data:
                    with self._hooks_lock:
                        pending_hooks = [h for h in self._hooks.get(session_id, []) if not h.executed]
                    for hook in pending_hooks:
                        hook.executed = True
                        logger.info("Self-healing: triggering unexecuted hook %s for completed session %s", hook.id, session_id)
                        art_list = result_data.get("artifacts") or []
                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(
                                self._execute_hook(
                                    hook,
                                    session_id,
                                    "",
                                    result_data,
                                    JarvisEvent(
                                        event_type=EventType.WORKER_COMPLETED,
                                        source="orchestrator",
                                        title="Self-Healing Hook Execution",
                                        summary=f"Executing hook {hook.id}",
                                        data={"session_id": session_id, **result_data},
                                    ),
                                    all_artifacts=art_list,
                                )
                            )
                        except RuntimeError:
                            bus = get_event_bus()
                            if bus._loop and bus._loop.is_running():
                                asyncio.run_coroutine_threadsafe(
                                    self._execute_hook(
                                        hook,
                                        session_id,
                                        "",
                                        result_data,
                                        JarvisEvent(
                                            event_type=EventType.WORKER_COMPLETED,
                                            source="orchestrator",
                                            title="Self-Healing Hook Execution",
                                            summary=f"Executing hook {hook.id}",
                                            data={"session_id": session_id, **result_data},
                                        ),
                                        all_artifacts=art_list,
                                    ),
                                    bus._loop,
                                )
        except Exception as exc:
            logger.debug("check_and_execute_pending_if_completed exception for %s: %s", session_id, exc)

    def register_hook(
        self,
        target_session_id: str,
        action_tool: str,
        action_params: Optional[Dict[str, Any]] = None,
        description: str = "",
        downstream_steps: Optional[List[Dict[str, Any]]] = None,
    ) -> ReactiveHook:
        """Register a follow-up action to execute as soon as target_session_id completes."""
        hook = ReactiveHook(
            target_session_id=target_session_id,
            action_tool=action_tool,
            action_params=action_params or {},
            description=description or f"Trigger {action_tool} on completion",
            downstream_steps=downstream_steps or [],
        )

        with self._hooks_lock:
            hook_list = self._hooks.setdefault(target_session_id, [])
            hook_list.append(hook)
            if action_tool != "fork" and downstream_steps:
                for ds in downstream_steps:
                    ds_tool = ds.get("tool")
                    if ds_tool:
                        child_hook = ReactiveHook(
                            target_session_id=target_session_id,
                            action_tool=ds_tool,
                            action_params=ds.get("params", {}),
                            description=ds.get("description", f"Trigger {ds_tool} on completion"),
                            downstream_steps=[],
                        )
                        hook_list.append(child_hook)

        bus = get_event_bus()
        bus.publish(
            JarvisEvent(
                event_type=EventType.TASK_CHAIN_REGISTERED,
                source="orchestrator",
                title="Chained Action Registered",
                summary=f"When worker [{target_session_id[:8]}] completes, automatically execute '{action_tool}'.",
                data={
                    "session_id": target_session_id,
                    "hook_id": hook.id,
                    "tool": action_tool,
                    "params": hook.action_params,
                    "downstream_steps": hook.downstream_steps,
                },
            )
        )
        logger.info(
            "Registered reactive hook %s for session %s -> tool %s (downstream: %d)",
            hook.id,
            target_session_id,
            action_tool,
            len(hook.downstream_steps),
        )
        self.check_and_execute_pending_if_completed(target_session_id)
        return hook

    def get_pending_hooks(self, session_id: str) -> List[ReactiveHook]:
        with self._hooks_lock:
            return [h for h in self._hooks.get(session_id, []) if not h.executed]

    async def _on_worker_failed(self, event: JarvisEvent) -> None:
        """Handle worker failure and abort registered hooks."""
        session_id = event.data.get("session_id") or event.metadata.get("session_id")
        if not session_id:
            return

        with self._hooks_lock:
            hooks = self._hooks.get(session_id, []).copy()

        err_msg = event.summary or "Worker task execution failed"
        bus = get_event_bus()

        for hook in hooks:
            if not hook.executed:
                hook.executed = True
                hook.error = f"Chained execution aborted: {err_msg}"
                bus.publish(
                    JarvisEvent(
                        event_type=EventType.AUTONOMOUS_ACTION_FAILED,
                        source="orchestrator",
                        title=f"Autonomous Action Aborted: {hook.action_tool}",
                        summary=f"Worker [{session_id[:8]}] failed. Aborting {hook.action_tool}.",
                        data={"session_id": session_id, "tool": hook.action_tool, "error": hook.error},
                    )
                )

    async def _on_worker_completed(self, event: JarvisEvent) -> None:
        """Handle worker completion and trigger all registered hooks."""
        session_id = event.data.get("session_id") or event.metadata.get("session_id")
        if not session_id:
            return

        with self._hooks_lock:
            hooks = self._hooks.get(session_id, []).copy()

        if not hooks:
            return

        artifacts = event.data.get("artifacts") or []
        output_data = event.data.get("output") or {}

        for hook in hooks:
            if hook.executed:
                continue

            hook.executed = True
            selected_artifact = self._select_artifact_for_hook(hook, session_id, artifacts, output_data)
            await self._execute_hook(hook, session_id, selected_artifact, output_data, event, artifacts)

    def _select_artifact_for_hook(
        self,
        hook: ReactiveHook,
        session_id: str,
        artifacts: List[str],
        output_data: Any,
    ) -> str:
        """Select the most relevant non-test business artifact for this specific hook."""
        from pathlib import Path
        import json, re

        def _is_test_file(p_str: str) -> bool:
            if not p_str:
                return True
            p = Path(p_str)
            name_lower = p.name.lower()
            return (
                name_lower.startswith(("test_", "verify_", "conftest"))
                or name_lower.endswith(("_test.py", "test.py"))
                or name_lower in ("implementation_plan.md", "task.json", "state.json", "result.json", "test_results.json")
            )

        search_context = f"{hook.description} {json.dumps(hook.action_params)}"

        # 1. Match explicit filenames mentioned in hook description / params from available artifacts
        for art in artifacts:
            if art and not _is_test_file(art):
                art_name = Path(art).name
                if art_name and art_name.lower() in search_context.lower():
                    return art

        # 2. Pick first non-test file from artifacts list
        for art in artifacts:
            if art and not _is_test_file(art):
                return art

        # 3. Fallback disk lookup
        from app.workers.base.session import WorkerSession
        session_dir = WorkerSession.SESSIONS_ROOT / session_id
        scope_dir = Path("D:/workspace")

        # 3a. Read objective from task.json
        obj = ""
        try:
            task_path = session_dir / "task.json"
            if task_path.is_file():
                task_data = json.loads(task_path.read_text(encoding="utf-8"))
                obj = task_data.get("objective", "")
                scope_str = task_data.get("fs_scope")
                if scope_str:
                    scope_dir = Path(scope_str)
        except Exception:
            pass

        full_context = f"{obj} {search_context}"

        # 3b. Match filenames mentioned in task objective or hook
        try:
            matches = re.findall(r"['\"]?([\w\-\.\\]+\.[a-zA-Z0-9]{1,8})['\"]?", full_context)
            for m in matches:
                if not _is_test_file(m):
                    cand = scope_dir / m
                    if cand.is_file():
                        return str(cand.resolve())
                    cand_raw = Path(m)
                    if cand_raw.is_file():
                        return str(cand_raw.resolve())
        except Exception:
            pass

        # 3c. Inspect worker session artifacts folder
        try:
            art_dir = session_dir / "artifacts"
            if art_dir.is_dir():
                art_files = [f for f in art_dir.iterdir() if f.is_file() and not _is_test_file(str(f))]
                if art_files:
                    art_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                    return str(art_files[0].resolve())
        except Exception:
            pass

        # 3d. Scan events.jsonl
        try:
            events_path = session_dir / "events.jsonl"
            if events_path.is_file():
                for line in reversed(events_path.read_text(encoding="utf-8").splitlines()):
                    if not line.strip():
                        continue
                    ev_data = json.loads(line)
                    d_str = json.dumps(ev_data)
                    f_matches = re.findall(r"([A-Za-z]:(?:\\\\|/|\\)[\w\-\.\s\\/]+\.[a-zA-Z0-9]{1,8})", d_str)
                    for fm in f_matches:
                        fp = Path(fm.replace("\\\\", "\\"))
                        if fp.is_file() and not _is_test_file(str(fp)):
                            return str(fp.resolve())
        except Exception:
            pass

        # 3e. Pick most recently modified non-test file in workspace
        try:
            if scope_dir.is_dir():
                ws_files = [f for f in scope_dir.iterdir() if f.is_file() and not _is_test_file(str(f))]
                if ws_files:
                    ws_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                    return str(ws_files[0].resolve())
        except Exception:
            pass

        return ""

    def _resolve_step_params(
        self,
        tool_name: str,
        raw_params: Dict[str, Any],
        artifact_path: str,
        session_id: str,
        output_data: Any,
    ) -> Dict[str, Any]:
        """Interpolate placeholders and infer missing file/attachment arguments."""
        from pathlib import Path

        def _interpolate_obj(val: Any) -> Any:
            if isinstance(val, str):
                s = val
                if "{worker.artifact}" in s or "{worker.artifact_path}" in s:
                    s = s.replace("{worker.artifact}", str(artifact_path)).replace(
                        "{worker.artifact_path}", str(artifact_path)
                    )
                if "{worker.session_id}" in s:
                    s = s.replace("{worker.session_id}", str(session_id))
                if "{worker.output}" in s:
                    s = s.replace("{worker.output}", str(output_data))
                return s
            elif isinstance(val, list):
                return [_interpolate_obj(item) for item in val]
            elif isinstance(val, dict):
                return {k: _interpolate_obj(v) for k, v in val.items()}
            return val

        resolved: Dict[str, Any] = _interpolate_obj(raw_params or {})

        # 1. Clean and infer attachments for send_email
        if tool_name == "send_email":
            raw_attachments = resolved.get("attachments") or []
            if isinstance(raw_attachments, list):
                clean_att = [
                    str(a).strip()
                    for a in raw_attachments
                    if str(a).strip() and str(a).strip() not in ("{worker.artifact}", "{worker.artifact_path}", "None")
                ]
                if not clean_att and artifact_path:
                    clean_att = [str(artifact_path)]
                resolved["attachments"] = clean_att
            elif artifact_path:
                resolved["attachments"] = [str(artifact_path)]

        # 2. Infer path for file operations if empty or unresolved placeholder
        if tool_name in ["send_file", "file_read", "file_extract", "read_file", "archive"]:
            curr_path = str(resolved.get("path", "")).strip()
            if not curr_path or curr_path in ("{worker.artifact}", "{worker.artifact_path}", "None"):
                if artifact_path:
                    resolved["path"] = str(artifact_path)

        # 3. Infer file_path / path / name for drive upload
        if tool_name == "upload_drive_file" or "drive" in tool_name:
            curr_fp = str(resolved.get("file_path", "")).strip()
            if not curr_fp or curr_fp in ("{worker.artifact}", "{worker.artifact_path}", "None"):
                if artifact_path:
                    resolved["file_path"] = str(artifact_path)
            if artifact_path and not resolved.get("name") and not resolved.get("file_name"):
                resolved["name"] = Path(artifact_path).name

        return resolved

    async def _execute_hook(
        self,
        hook: ReactiveHook,
        session_id: str,
        artifact_path: str,
        output_data: Any,
        trigger_event: JarvisEvent,
        all_artifacts: Optional[List[str]] = None,
    ) -> None:
        bus = get_event_bus()
        all_artifacts = all_artifacts or []

        if not artifact_path:
            artifact_path = self._select_artifact_for_hook(hook, session_id, all_artifacts, output_data)

        tool_name = hook.action_tool
        resolved_params = self._resolve_step_params(tool_name, hook.action_params, artifact_path, session_id, output_data)

        bus.publish(
            JarvisEvent(
                event_type=EventType.AUTONOMOUS_ACTION_STARTED,
                source="orchestrator",
                title=f"Executing Autonomous Follow-Up: {tool_name}",
                summary=f"Worker [{session_id[:8]}] finished. Triggering {tool_name} with parameters.",
                data={"session_id": session_id, "tool": tool_name, "params": resolved_params},
            )
        )

        try:
            from app.core.execution_engine import ExecutionEngine
            engine = ExecutionEngine(registry)
            tool_result = await engine.run(tool_name, resolved_params)

            if tool_result.success:
                hook.result = tool_result.data
                bus.publish(
                    JarvisEvent(
                        event_type=EventType.AUTONOMOUS_ACTION_EXECUTED,
                        source="orchestrator",
                        title=f"Autonomous Action Succeeded: {tool_name}",
                        summary=f"Successfully executed '{tool_name}' following completion of worker [{session_id[:8]}].",
                        data={
                            "session_id": session_id,
                            "tool": tool_name,
                            "params": resolved_params,
                            "result": tool_result.data,
                        },
                    )
                )
                logger.info("Reactive hook %s executed successfully for %s", hook.id, session_id)

                # Process downstream steps
                if tool_name == "fork":
                    new_session_id = tool_result.data.get("session_id") if isinstance(tool_result.data, dict) else None
                    if new_session_id and hook.downstream_steps:
                        next_step = hook.downstream_steps[0]
                        remaining_downstream = hook.downstream_steps[1:] if len(hook.downstream_steps) > 1 else []
                        self.register_hook(
                            target_session_id=new_session_id,
                            action_tool=next_step["tool"],
                            action_params=next_step.get("params", {}),
                            description=next_step.get("description", ""),
                            downstream_steps=remaining_downstream,
                        )
                elif tool_name != "fork" and hook.downstream_steps:
                    for rem_idx, rem_step in enumerate(hook.downstream_steps):
                        rem_tool = rem_step["tool"]
                        rem_params = rem_step.get("params", {})

                        with self._hooks_lock:
                            child_hooks = [h for h in self._hooks.get(session_id, []) if h.action_tool == rem_tool and not h.executed]
                            child_hook = child_hooks[0] if child_hooks else None

                        if rem_tool == "fork":
                            rem_downstream = hook.downstream_steps[rem_idx + 1:] if rem_idx + 1 < len(hook.downstream_steps) else []
                            fork_res = await engine.run("fork", rem_params)
                            if fork_res.success and isinstance(fork_res.data, dict) and fork_res.data.get("session_id") and rem_downstream:
                                self.register_hook(
                                    target_session_id=fork_res.data["session_id"],
                                    action_tool=rem_downstream[0]["tool"],
                                    action_params=rem_downstream[0].get("params", {}),
                                    description=rem_downstream[0].get("description", ""),
                                    downstream_steps=rem_downstream[1:],
                                )
                            if child_hook:
                                child_hook.executed = True
                                child_hook.result = fork_res.data if fork_res.success else None
                                child_hook.error = str(fork_res.error) if not fork_res.success else None
                            break
                        else:
                            resolved_rem_params = self._resolve_step_params(rem_tool, rem_params, artifact_path, session_id, output_data)
                            bus.publish(
                                JarvisEvent(
                                    event_type=EventType.AUTONOMOUS_ACTION_STARTED,
                                    source="orchestrator",
                                    title=f"Executing Autonomous Follow-Up: {rem_tool}",
                                    summary=f"Worker [{session_id[:8]}] finished. Triggering {rem_tool} with parameters.",
                                    data={"session_id": session_id, "tool": rem_tool, "params": resolved_rem_params},
                                )
                            )
                            rem_result = await engine.run(rem_tool, resolved_rem_params)
                            if rem_result.success:
                                if child_hook:
                                    child_hook.executed = True
                                    child_hook.result = rem_result.data
                                bus.publish(
                                    JarvisEvent(
                                        event_type=EventType.AUTONOMOUS_ACTION_EXECUTED,
                                        source="orchestrator",
                                        title=f"Autonomous Action Succeeded: {rem_tool}",
                                        summary=f"Successfully executed '{rem_tool}' for worker [{session_id[:8]}].",
                                        data={
                                            "session_id": session_id,
                                            "tool": rem_tool,
                                            "params": resolved_rem_params,
                                            "result": rem_result.data,
                                        },
                                    )
                                )
                            else:
                                if child_hook:
                                    child_hook.executed = True
                                    child_hook.error = str(rem_result.error)
                                bus.publish(
                                    JarvisEvent(
                                        event_type=EventType.AUTONOMOUS_ACTION_FAILED,
                                        source="orchestrator",
                                        title=f"Autonomous Action Failed: {rem_tool}",
                                        summary=f"Failed executing '{rem_tool}' for worker [{session_id[:8]}]: {rem_result.error}",
                                        data={"session_id": session_id, "tool": rem_tool, "error": rem_result.error},
                                    )
                                )
                                break
            else:
                hook.error = str(tool_result.error)
                bus.publish(
                    JarvisEvent(
                        event_type=EventType.AUTONOMOUS_ACTION_FAILED,
                        source="orchestrator",
                        title=f"Autonomous Action Failed: {tool_name}",
                        summary=f"Failed executing '{tool_name}' for worker [{session_id[:8]}]: {tool_result.error}",
                        data={"session_id": session_id, "tool": tool_name, "error": tool_result.error},
                    )
                )
                # Abort any downstream steps
                if hook.downstream_steps:
                    for rem_step in hook.downstream_steps:
                        rem_tool = rem_step["tool"]
                        with self._hooks_lock:
                            child_hooks = [h for h in self._hooks.get(session_id, []) if h.action_tool == rem_tool and not h.executed]
                            if child_hooks:
                                child_hooks[0].executed = True
                                child_hooks[0].error = f"Aborted: {tool_name} failed"
                        bus.publish(
                            JarvisEvent(
                                event_type=EventType.AUTONOMOUS_ACTION_FAILED,
                                source="orchestrator",
                                title=f"Autonomous Action Aborted: {rem_tool}",
                                summary=f"Prior action '{tool_name}' failed. Aborting '{rem_tool}'.",
                                data={"session_id": session_id, "tool": rem_tool, "error": f"Aborted: {tool_name} failed"},
                            )
                        )
        except Exception as exc:
            logger.error("Error executing reactive hook %s: %s", hook.id, exc, exc_info=True)
            hook.error = str(exc)
            bus.publish(
                JarvisEvent(
                    event_type=EventType.AUTONOMOUS_ACTION_FAILED,
                    source="orchestrator",
                    title=f"Autonomous Action Error: {tool_name}",
                    summary=f"Exception executing '{tool_name}' for worker [{session_id[:8]}]: {str(exc)}",
                    data={"session_id": session_id, "tool": tool_name, "error": str(exc)},
                )
            )

    def get_hooks(self, session_id: Optional[str] = None) -> List[ReactiveHook]:
        if session_id:
            self.check_and_execute_pending_if_completed(session_id)
        with self._hooks_lock:
            if session_id:
                return [h for h in self._hooks.get(session_id, [])]
            all_hooks: List[ReactiveHook] = []
            for h_list in self._hooks.values():
                all_hooks.extend(h_list)
            return all_hooks


# Global singleton instance
_orchestrator: Optional[TaskOrchestrator] = None


def get_orchestrator() -> TaskOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TaskOrchestrator()
        _orchestrator.start()
    elif not _orchestrator._listening:
        _orchestrator.start()
    return _orchestrator
