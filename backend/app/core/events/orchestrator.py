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
        self._listening = True
        logger.info("TaskOrchestrator initialized and listening for worker completion events.")

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
            self._hooks.setdefault(target_session_id, []).append(hook)

        bus = get_event_bus()
        bus.publish(
            JarvisEvent(
                event_type=EventType.TASK_CHAIN_REGISTERED,
                source="orchestrator",
                title="Chained Action Registered",
                summary=f"When worker [{target_session_id[:8]}] completes, automatically execute '{action_tool}'.",
                data={"session_id": target_session_id, "hook_id": hook.id, "tool": action_tool, "params": hook.action_params, "downstream_steps": hook.downstream_steps},
            )
        )
        logger.info(
            "Registered reactive hook %s for session %s -> tool %s (downstream: %d)",
            hook.id,
            target_session_id,
            action_tool,
            len(hook.downstream_steps),
        )
        return hook

    def get_pending_hooks(self, session_id: str) -> List[ReactiveHook]:
        with self._hooks_lock:
            return [h for h in self._hooks.get(session_id, []) if not h.executed]

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
        first_artifact = artifacts[0] if artifacts else ""
        output_data = event.data.get("output") or {}

        for hook in hooks:
            if hook.executed:
                continue

            hook.executed = True
            await self._execute_hook(hook, session_id, first_artifact, output_data, event)

    async def _execute_hook(
        self,
        hook: ReactiveHook,
        session_id: str,
        artifact_path: str,
        output_data: Any,
        trigger_event: JarvisEvent,
    ) -> None:
        tool_name = hook.action_tool
        bus = get_event_bus()

        # Smart artifact resolution if artifact_path was not explicitly provided in the event
        if not artifact_path or str(artifact_path).strip() in ("", "{worker.artifact}", "{worker.artifact_path}", "None"):
            artifact_path = ""
            from pathlib import Path
            import json, re, time
            from app.workers.base.session import WorkerSession

            session_dir = WorkerSession.SESSIONS_ROOT / session_id
            scope_dir = Path("D:/workspace")

            # 1. Check worker session artifacts folder
            try:
                artifacts_dir = session_dir / "artifacts"
                if artifacts_dir.is_dir():
                    art_files = [f for f in artifacts_dir.iterdir() if f.is_file()]
                    if art_files:
                        art_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                        artifact_path = str(art_files[0].resolve())
            except Exception:
                pass

            # 2. Extract objective & fs_scope from task.json
            obj = ""
            if not artifact_path:
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

            # 3. Check events.jsonl for file paths touched by worker tools
            if not artifact_path:
                try:
                    events_path = session_dir / "events.jsonl"
                    if events_path.is_file():
                        for line in reversed(events_path.read_text(encoding="utf-8").splitlines()):
                            if not line.strip():
                                continue
                            ev_data = json.loads(line)
                            # Scan params and data
                            d_str = json.dumps(ev_data)
                            f_matches = re.findall(r"['\"]?([A-Za-z]:[/\\][\w\-\.\\/]+\.[a-zA-Z0-9]{1,6})['\"]?", d_str)
                            for fm in f_matches:
                                fp = Path(fm)
                                if fp.is_file() and not str(fp).endswith(".json") and not str(fp).endswith(".jsonl"):
                                    artifact_path = str(fp.resolve())
                                    break
                            if artifact_path:
                                break
                except Exception:
                    pass

            # 4. Check workspace scope and match filenames mentioned in contract objective or hook
            if not artifact_path:
                try:
                    matches = re.findall(r"['\"]?([\w\-\.\\]+\.[a-zA-Z0-9]{1,6})['\"]?", f"{obj} {hook.description}")
                    for m in matches:
                        cand = scope_dir / m
                        if cand.is_file():
                            artifact_path = str(cand.resolve())
                            break
                        cand_raw = Path(m)
                        if cand_raw.is_file():
                            artifact_path = str(cand_raw.resolve())
                            break
                except Exception:
                    pass

            # 5. Fallback: pick the most recently created/modified file in the workspace
            if not artifact_path and scope_dir.is_dir():
                try:
                    now = time.time()
                    ws_files = [f for f in scope_dir.iterdir() if f.is_file() and not f.name.startswith(".")]
                    if ws_files:
                        ws_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                        # Check if modified within the last 15 minutes (or take most recent)
                        artifact_path = str(ws_files[0].resolve())
                except Exception:
                    pass

        # Interpolate variables in params
        resolved_params: Dict[str, Any] = {}
        for k, v in hook.action_params.items():
            if isinstance(v, str):
                val = v
                if "{worker.artifact}" in val or "{worker.artifact_path}" in val:
                    val = val.replace("{worker.artifact}", str(artifact_path)).replace(
                        "{worker.artifact_path}", str(artifact_path)
                    )
                if "{worker.session_id}" in val:
                    val = val.replace("{worker.session_id}", str(session_id))
                if "{worker.output}" in val:
                    val = val.replace("{worker.output}", str(output_data))
                resolved_params[k] = val
            else:
                resolved_params[k] = v

        # If a path was required by tool (e.g. send_file) but empty or omitted, infer from artifact_path
        if tool_name in ["send_file", "file_read", "file_extract", "read_file", "archive"]:
            curr_path = str(resolved_params.get("path", "")).strip()
            if not curr_path or curr_path in ("{worker.artifact}", "{worker.artifact_path}"):
                if artifact_path:
                    resolved_params["path"] = str(artifact_path)

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
                # If tool_name is "fork", a new worker session was created!
                # Chain the downstream pipeline onto this newly created session!
                new_session_id = tool_result.data.get("session_id") if isinstance(tool_result.data, dict) else None
                if tool_name == "fork" and new_session_id and hook.downstream_steps:
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
                    # Non-worker tool executed; proceed to sequentially execute any remaining downstream steps
                    for rem_idx, rem_step in enumerate(hook.downstream_steps):
                        rem_tool = rem_step["tool"]
                        rem_params = rem_step.get("params", {})
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
                            break
                        else:
                            await engine.run(rem_tool, rem_params)

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
            else:
                bus.publish(
                    JarvisEvent(
                        event_type=EventType.AUTONOMOUS_ACTION_FAILED,
                        source="orchestrator",
                        title=f"Autonomous Action Failed: {tool_name}",
                        summary=f"Failed executing '{tool_name}' for worker [{session_id[:8]}]: {tool_result.error}",
                        data={"session_id": session_id, "tool": tool_name, "error": tool_result.error},
                    )
                )
        except Exception as exc:
            logger.error("Error executing reactive hook %s: %s", hook.id, exc, exc_info=True)
            bus.publish(
                JarvisEvent(
                    event_type=EventType.AUTONOMOUS_ACTION_FAILED,
                    source="orchestrator",
                    title=f"Autonomous Action Error: {tool_name}",
                    summary=f"Exception executing '{tool_name}' for worker [{session_id[:8]}]: {str(exc)}",
                    data={"session_id": session_id, "tool": tool_name, "error": str(exc)},
                )
            )


# Global singleton instance
_orchestrator: Optional[TaskOrchestrator] = None


def get_orchestrator() -> TaskOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TaskOrchestrator()
    return _orchestrator
