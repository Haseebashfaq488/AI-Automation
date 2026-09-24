import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.workers.base import bus as bus_mod
from app.workers.base.contract import TaskContract
from app.workers.base.engine import WorkerEngine
from app.registry import registry

router = APIRouter(prefix="/workers", tags=["workers"])

# In-process engine store: session_id → WorkerEngine
# (single-process dev setup; swap for Redis/DB in a multi-worker deployment)
_engines: Dict[str, WorkerEngine] = {}


def _default_scope() -> str:
    return os.path.abspath(os.sep)


class ForkRequest(BaseModel):
    objective: str
    worker_type: str = "antigravity_worker"
    model: Optional[str] = None
    requirements: List[str] = []
    constraints: List[str] = []
    success_criteria: List[str] = []
    fs_scope: str = Field(default_factory=_default_scope)
    allowed_tools: List[str] = []
    max_steps: int = 20
    requires_plan_approval: bool = True


class InterveneRequest(BaseModel):
    message: str


class ApprovePlanRequest(BaseModel):
    plan: Optional[str] = None


class RejectPlanRequest(BaseModel):
    feedback: str


class OpenTerminalRequest(BaseModel):
    directory: Optional[str] = "D:/Ai automation backend"
    prompt: Optional[str] = None


# ── Endpoints ────────────────────────────────────────────────────────────


@router.post("/open-terminal")
async def open_terminal(payload: Optional[OpenTerminalRequest] = None):
    """Directly launch a visible, interactive OpenCode CLI window on the user's desktop."""
    import subprocess
    import sys
    from app.workers.opencode_worker.agent.config import get_opencode_binary

    target_dir = payload.directory if payload and payload.directory else "D:/Ai automation backend"
    if not os.path.exists(target_dir):
        target_dir = "D:/Ai automation backend"

    bat_file = os.path.join("D:\\Ai automation backend", "launch_opencode.bat")

    try:
        if sys.platform == "win32":
            if os.path.isfile(bat_file):
                # NOTE: do NOT launch the .bat via explorer.exe — explorer.exe
                # silently drops quoted paths that contain spaces (this repo
                # lives in "D:\Ai automation backend"), so nothing opened.
                # `start` always creates a NEW, visible console window (never
                # background) and `/max` maximizes it so it can't hide behind
                # the browser. First quoted arg = window title (mandatory).
                subprocess.Popen(
                    f'start "Jarvis OpenCode CLI" /max "{bat_file}"',
                    shell=True,
                )
            else:
                binary = get_opencode_binary() or "opencode"
                subprocess.Popen(
                    f'start "OpenCode CLI" /max powershell.exe -NoExit '
                    f'-Command "Set-Location -LiteralPath \'{target_dir}\'; & \'{binary}\'"',
                    shell=True,
                )
        else:
            binary = get_opencode_binary() or "opencode"
            subprocess.Popen([binary], cwd=target_dir)

        return {
            "status": "launched",
            "message": f"OpenCode CLI terminal launched in {target_dir}",
            "directory": target_dir,
            "launcher": bat_file,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to launch OpenCode terminal: {exc}")


@router.post("/open-agy-terminal")
async def open_agy_terminal(payload: Optional[OpenTerminalRequest] = None):
    """Directly launch a visible, interactive Antigravity CLI (`agy`) window on the user's desktop."""
    import subprocess
    import sys
    from app.workers.antigravity_worker.agent.config import get_agy_binary

    target_dir = payload.directory if payload and payload.directory else "D:/AI-Automation"
    if not os.path.exists(target_dir):
        target_dir = "D:/AI-Automation"

    binary = get_agy_binary() or os.path.expandvars(r"%LOCALAPPDATA%\agy\bin\agy.exe")

    try:
        if sys.platform == "win32":
            subprocess.Popen(
                f'start "Antigravity CLI (agy)" /max powershell.exe -NoExit '
                f'-Command "Set-Location -LiteralPath \'{target_dir}\'; & \'{binary}\'"',
                shell=True,
            )
        else:
            subprocess.Popen([binary], cwd=target_dir)

        return {
            "status": "launched",
            "message": f"Antigravity CLI (agy) window launched in {target_dir}",
            "directory": target_dir,
            "binary": binary,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to launch Antigravity CLI terminal: {exc}")


@router.post("/open-desktop")
async def open_desktop():
    """Launch the OpenCode Desktop GUI application on Windows if installed."""
    import subprocess
    import sys

    desktop_app = os.path.expandvars(r"%LOCALAPPDATA%\Programs\@opencode-aidesktop\OpenCode.exe")
    if not os.path.isfile(desktop_app):
        raise HTTPException(status_code=404, detail="OpenCode Desktop GUI app is not installed at default location.")

    try:
        if sys.platform == "win32":
            subprocess.Popen([desktop_app], shell=False)
        return {
            "status": "launched",
            "message": "OpenCode Desktop Application launched.",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to launch OpenCode Desktop: {exc}")



@router.get("")
@router.get("/")
@router.get("/list")
async def list_workers():
    """Summary state of every known worker session (parent dashboard).

    Merges live in‑memory engines with sessions persisted on disk so workers
    survive a backend restart.
    """
    workers = [{"session_id": sid, **eng.get_state()} for sid, eng in _engines.items()]
    seen = {w["session_id"] for w in workers}
    for session_id, state in _disk_sessions().items():
        if session_id not in seen:
            workers.append({"session_id": session_id, **state})
    return {"workers": workers}


@router.delete("")
@router.delete("/")
@router.post("/clear")
async def clear_all_workers():
    """Purge all on-disk worker sessions and clear the in-memory engine cache."""
    import shutil
    from app.workers.base.session import WorkerSession

    for eng in list(_engines.values()):
        try:
            eng.cancel()
        except Exception:
            pass
    _engines.clear()

    root = WorkerSession.SESSIONS_ROOT
    purged_count = 0
    if root.is_dir():
        for child in list(root.iterdir()):
            if child.is_dir():
                try:
                    shutil.rmtree(child)
                    purged_count += 1
                except Exception:
                    pass

    return {"status": "cleared", "purged_sessions_count": purged_count}



@router.post("/fork")
async def fork_worker(payload: ForkRequest):
    """Create (fork) a new worker session and start its loop in the background."""
    try:
        contract = TaskContract(
            objective=payload.objective,
            requirements=payload.requirements,
            constraints=payload.constraints,
            success_criteria=payload.success_criteria,
            fs_scope=payload.fs_scope,
            allowed_tools=payload.allowed_tools,
            max_steps=payload.max_steps,
            model=payload.model,
            requires_plan_approval=payload.requires_plan_approval,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid contract: {exc}")

    return await launch_worker(contract, worker_type=payload.worker_type)


async def launch_worker(contract: TaskContract, worker_type: str = "antigravity_worker") -> Dict:
    """Create + start a worker engine and register it for polling/SSE.

    Shared by the /fork route and the agent's `fork` tool so both produce
    identically queryable sessions.
    """
    # Auto-detect existing handover in workspace if not explicitly provided
    if not contract.prior_handover:
        try:
            scope_dir = Path(contract.fs_scope)
            handover_file = scope_dir / "handover.json"
            if handover_file.is_file():
                contract.prior_handover = json.loads(handover_file.read_text(encoding="utf-8"))
                contract.is_refinement = True
            elif (scope_dir / "SESSION_HANDOVER.md").is_file():
                contract.prior_handover = {"summary": (scope_dir / "SESSION_HANDOVER.md").read_text(encoding="utf-8")}
                contract.is_refinement = True
        except Exception:
            pass

    # Discover living documentation (subfolder README.md files)
    if not contract.folder_manifests:
        try:
            scope_dir = Path(contract.fs_scope)
            if scope_dir.is_dir():
                manifests = []
                for p in scope_dir.rglob("README.md"):
                    if p.is_file():
                        try:
                            manifests.append(str(p.relative_to(scope_dir)))
                        except Exception:
                            manifests.append(str(p))
                contract.folder_manifests = manifests
        except Exception:
            pass

    eng = WorkerEngine(registry, agent_factory=_agent_factory_for(worker_type))
    _engines[eng.session_id()] = eng
    state = await eng.run(contract)
    return {"session_id": eng.session_id(), **state}


def _disk_sessions() -> Dict[str, Dict]:
    """Worker states recovered from disk (sessions whose engine is gone,
    e.g. after a backend restart)."""
    from app.workers.base.session import WorkerSession

    found: Dict[str, Dict] = {}
    root = WorkerSession.SESSIONS_ROOT
    if not root.is_dir():
        return found
    for child in sorted(root.iterdir()):
        if not child.is_dir() or not (child / "task.json").is_file():
            continue
        session = WorkerSession(child.name)
        state = session.read_state()
        has_result = (child / "result.json").is_file() and session.read_result()
        contract_info: Dict[str, Any] = {}
        try:
            task_data = session.read_task()
            contract_info = {
                "objective": task_data.objective,
                "fs_scope": task_data.fs_scope,
                "allowed_tools": task_data.allowed_tools,
                "max_steps": task_data.max_steps,
                "plan_status": task_data.plan_status,
            }
        except Exception:
            pass

        found[child.name] = {
            "status": "completed" if has_result else (state.get("status") or "unknown"),
            "progress_percent": state.get("progress_percent", 100 if has_result else 0),
            "current_step": state.get("current_step"),
            "completed": state.get("completed", []),
            "remaining": state.get("remaining", []),
            "errors": state.get("errors", []),
            "implementation_plan": session.read_plan(),
            "test_results": session.read_test_results(),
            **contract_info,
        }
    return found


def _agent_factory_for(worker_type: str):
    """Return an agent factory for the worker type, or None (placeholder loop)."""
    if worker_type in ("opencode_worker", "opencode"):
        from app.workers.opencode_worker.agent.worker_agent import OpenCodeWorkerAgent

        def factory(contract: TaskContract):
            return OpenCodeWorkerAgent(
                objective=contract.objective,
                allowed_tools=contract.allowed_tools,
                fs_scope=contract.fs_scope,
                requirements=contract.requirements,
                constraints=contract.constraints,
                success_criteria=contract.success_criteria,
            )

        return factory

    if worker_type in ("antigravity_worker", "antigravity", "agy"):
        from app.workers.antigravity_worker.agent.worker_agent import AntigravityWorkerAgent

        def factory(contract: TaskContract):
            return AntigravityWorkerAgent(
                objective=contract.objective,
                allowed_tools=contract.allowed_tools,
                fs_scope=contract.fs_scope,
                requirements=contract.requirements,
                constraints=contract.constraints,
                success_criteria=contract.success_criteria,
                model=contract.model,
                master_prompt=contract.master_prompt,
                worker_session_id=contract.task_id,
                requires_plan_approval=contract.requires_plan_approval,
                prior_handover=contract.prior_handover,
                is_refinement=contract.is_refinement,
                folder_manifests=contract.folder_manifests,
            )

        return factory

    return None


@router.get("/{session_id}/supervisor-status")
async def get_worker_supervisor_status(session_id: str):
    """Retrieve active stream guardian supervision metrics and violations."""
    eng = _engines.get(session_id)
    if eng:
        return {"session_id": session_id, **eng.get_guardian_status()}
    return {"session_id": session_id, "status": "guardian_inactive_or_completed"}


@router.get("/{session_id}/resolution")
async def get_worker_resolution(session_id: str):
    """Retrieve Jarvis's post-execution evaluation and completion verdict."""
    from app.modules.antigravity.brain import get_brain_manager
    from app.workers.base.session import WorkerSession

    eng = _engines.get(session_id)
    result_data = eng.get_result() if eng else None
    
    if not result_data:
        session = WorkerSession(session_id)
        if (session.path / "result.json").is_file():
            result_data = session.read_result()

    if not result_data:
        raise HTTPException(status_code=404, detail="Worker result not yet available")

    # Evaluate resolution via brain manager
    brain = get_brain_manager()
    session = WorkerSession(session_id)
    task_contract = session.read_task()
    evaluation = brain.evaluate_worker_completion(session_id, task_contract, result_data)
    return {"session_id": session_id, "evaluation": evaluation}


@router.get("/{session_id}")
async def get_worker(session_id: str):
    eng = _engines.get(session_id)
    if eng:
        return {"session_id": session_id, **eng.get_state()}
    # Fall back to the on‑disk session (backend restarted while it existed).
    disk = _disk_sessions().get(session_id)
    if disk is None:
        raise HTTPException(status_code=404, detail="Worker session not found")
    return {"session_id": session_id, **disk}


@router.get("/{session_id}/result")
async def get_worker_result(session_id: str):
    eng = _engines.get(session_id)
    if eng:
        return {"session_id": session_id, "result": eng.get_result()}
    from app.workers.base.session import WorkerSession

    session = WorkerSession(session_id)
    if not (session.path / "result.json").is_file():
        raise HTTPException(status_code=404, detail="Worker session not found")
    return {"session_id": session_id, "result": session.read_result()}


@router.post("/{session_id}/approve-plan")
async def approve_worker_plan(session_id: str, payload: Optional[ApprovePlanRequest] = None):
    """Approve the worker's implementation plan and trigger execution."""
    eng = _engines.get(session_id)
    if not eng:
        raise HTTPException(status_code=404, detail="Worker session not found")
    plan_override = payload.plan if payload else None
    eng.approve_plan(plan_override)
    return {"status": "plan approved", "session_id": session_id}


@router.post("/{session_id}/reject-plan")
async def reject_worker_plan(session_id: str, payload: RejectPlanRequest):
    """Reject or request revisions to the worker's implementation plan."""
    eng = _engines.get(session_id)
    if not eng:
        raise HTTPException(status_code=404, detail="Worker session not found")
    eng.reject_plan(payload.feedback)
    return {"status": "plan rejected with feedback", "session_id": session_id}


@router.get("/{session_id}/plan")
async def get_worker_plan(session_id: str):
    """Retrieve the worker's implementation plan."""
    from app.workers.base.session import WorkerSession

    eng = _engines.get(session_id)
    if eng:
        plan = eng._implementation_plan or (eng._session.read_plan() if eng._session else "")
        return {"session_id": session_id, "plan": plan}

    session = WorkerSession(session_id)
    plan = session.read_plan()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found for session")
    return {"session_id": session_id, "plan": plan}


@router.get("/{session_id}/test-results")
async def get_worker_test_results(session_id: str):
    """Retrieve the worker's automated self-testing results."""
    from app.workers.base.session import WorkerSession

    eng = _engines.get(session_id)
    if eng:
        results = eng._test_results or (eng._session.read_test_results() if eng._session else {})
        return {"session_id": session_id, "test_results": results}

    session = WorkerSession(session_id)
    results = session.read_test_results()
    if not results:
        raise HTTPException(status_code=404, detail="Test results not found for session")
    return {"session_id": session_id, "test_results": results}


@router.post("/{session_id}/intervene")
async def intervene_worker(session_id: str, payload: InterveneRequest):
    eng = _engines.get(session_id)
    if not eng:
        raise HTTPException(status_code=404, detail="Worker session not found")
    eng.intervene(payload.message)
    return {"status": "intervention recorded"}


@router.post("/{session_id}/cancel")
async def cancel_worker(session_id: str):
    eng = _engines.get(session_id)
    if not eng:
        raise HTTPException(status_code=404, detail="Worker session not found")
    eng.cancel()
    return {"status": "cancellation requested"}


@router.get("/{session_id}/artifacts")
async def list_worker_artifacts(session_id: str):
    """List files created in the worker's artifacts directory."""
    from app.workers.base.session import WorkerSession

    eng = _engines.get(session_id)
    session_dir = (eng._session.path if eng and eng._session else WorkerSession.SESSIONS_ROOT / session_id)
    artifacts_dir = session_dir / "artifacts"
    if not artifacts_dir.is_dir():
        return {"artifacts": []}

    files = []
    for item in sorted(artifacts_dir.iterdir()):
        if item.is_file():
            files.append({
                "name": item.name,
                "size_bytes": item.stat().st_size,
                "download_url": f"/workers/{session_id}/artifacts/{item.name}",
            })
    return {"artifacts": files}


@router.get("/{session_id}/artifacts/{filename}")
async def get_worker_artifact_file(session_id: str, filename: str):
    """Download a file created in the worker's artifacts directory."""
    from app.workers.base.session import WorkerSession

    eng = _engines.get(session_id)
    session_dir = (eng._session.path if eng and eng._session else WorkerSession.SESSIONS_ROOT / session_id)
    artifacts_dir = (session_dir / "artifacts").resolve()
    file_path = (artifacts_dir / filename).resolve()
    if not str(file_path).startswith(str(artifacts_dir)):
        raise HTTPException(status_code=403, detail="Forbidden")
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Artifact file not found")
    return FileResponse(file_path, filename=filename)


@router.get("/{session_id}/events")
async def worker_events(session_id: str, request: Request):
    """SSE stream of this worker's events (live activity feed with disk replay fallback)."""
    from app.workers.base.session import WorkerSession

    eng = _engines.get(session_id)
    session_dir = (eng._session.path if eng and eng._session else WorkerSession.SESSIONS_ROOT / session_id)
    events_file = session_dir / "events.jsonl"
    if not eng and not events_file.is_file():
        raise HTTPException(status_code=404, detail="Worker session not found")

    queue: asyncio.Queue = asyncio.Queue(maxsize=200)

    def _callback(event_type: str, data: dict) -> None:
        try:
            queue.put_nowait({"type": event_type, "data": data})
        except asyncio.QueueFull:
            pass  # backpressure: drop when client is slow

    if eng:
        bus_mod.on(session_id, _callback)

    async def event_generator():
        ticks = 0
        completed_at: Optional[float] = None
        try:
            # Replay events that fired before client connected or from disk
            if events_file.is_file():
                for line in events_file.read_text(encoding="utf-8").strip().splitlines():
                    if not line:
                        continue
                    yield f"data: {line}\n\n"
                    if '"WORK_COMPLETED"' in line:
                        completed_at = 0.0

            # If the session is already finished on disk, exit cleanly after replay
            if not eng:
                return

            while not await request.is_disconnected():
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event["type"] == "WORK_COMPLETED":
                        completed_at = ticks
                except asyncio.TimeoutError:
                    ticks += 1
                    # After completion, linger briefly for trailing events then close
                    if completed_at is not None and ticks - completed_at >= 3:
                        break
                    if ticks % 30 == 0:
                        yield ": keep-alive\n\n"  # SSE comment every ~30s
        finally:
            if eng:
                try:
                    bus_mod._bus.get(session_id, []).remove(_callback)
                except (ValueError, AttributeError):
                    pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/{session_id}/stream")
async def worker_stream(session_id: str, request: Request):
    """Real-time SSE stream of raw Antigravity CLI events (step_update deltas, tool calls, and result)."""
    from app.workers.base.session import WorkerSession

    eng = _engines.get(session_id)
    session_dir = (
        eng._session.path if eng and eng._session else WorkerSession.SESSIONS_ROOT / session_id
    )

    if not eng and not (session_dir / "task.json").is_file():
        raise HTTPException(status_code=404, detail="Worker session not found")

    # If the session is already completed before connection, return final result
    is_completed = False
    result_data = None
    if eng:
        state = eng.get_state()
        if state.get("status") in ("completed", "cancelled"):
            is_completed = True
            result_data = eng.get_result()
    else:
        result_file = session_dir / "result.json"
        if result_file.is_file():
            is_completed = True
            try:
                result_data = json.loads(result_file.read_text(encoding="utf-8"))
            except Exception:
                result_data = {}

    if is_completed:
        async def finished_generator():
            events_file = session_dir / "events.jsonl"
            if events_file.is_file():
                for line in events_file.read_text(encoding="utf-8").strip().splitlines():
                    if line:
                        yield f"data: {line}\n\n"
            yield f"data: {json.dumps({'event': 'result', 'result': result_data or {}})}\n\n"

        return StreamingResponse(
            finished_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    queue = bus_mod.subscribe(session_id)

    async def stream_generator():
        try:
            while not await request.is_disconnected():
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(event)}\n\n"

                    # If this is the terminal result event, finish streaming cleanly
                    if isinstance(event, dict):
                        if event.get("event") == "result" or event.get("type") == "WORK_COMPLETED":
                            break
                except asyncio.TimeoutError:
                    # Check if engine finished while waiting
                    if eng:
                        cur_status = eng.get_state().get("status")
                        if cur_status in ("completed", "cancelled") and queue.empty():
                            final_res = eng.get_result()
                            yield f"data: {json.dumps({'event': 'result', 'result': final_res or {}})}\n\n"
                            break
                    # SSE comment keep-alive heartbeat every 30s
                    yield ": keep-alive\n\n"
        finally:
            bus_mod.unsubscribe(session_id, queue)

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def get_engine(session_id: str) -> Optional[WorkerEngine]:
    """Used by the agent route to look up engines after delegation."""
    return _engines.get(session_id)