import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.modules.opencode.adapter import OpenCodeAdapter
from app.modules.memory import ChatMemory, LongTermMemory
from app.core.execution_engine import ExecutionEngine
from app.registry import registry

router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger("jarvis.agent")

# Adapter is created lazily so the app boots smoothly.
_adapter: Optional[Any] = None


def _get_adapter() -> Any:
    global _adapter
    if _adapter is None:
        from app.workers.antigravity_worker.agent import config as agy_config
        if agy_config.get_agy_binary():
            from app.modules.antigravity.brain import get_brain_manager
            _adapter = get_brain_manager(registry=registry)
        else:
            try:
                _adapter = OpenCodeAdapter(registry=registry)
            except RuntimeError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _adapter


engine = ExecutionEngine(registry)

# In-memory plan cache: plan_id -> list of steps
_plan_cache: Dict[str, List[Dict[str, Any]]] = {}

# Memory: short-term per-session chat memory + long-term persistent memory.
# Module-level instances so tests can swap them (e.g. in-memory DB).
chat_memory = ChatMemory(max_messages=20)
long_term_memory = LongTermMemory(limit=100)

# Memory extraction runs every N conversational turns to avoid the ~20s agy
# overhead on every message. Plan confirmations always extract regardless.
_turn_counter: int = 0
MEMORY_EXTRACTION_INTERVAL: int = 5  # change to 10 if you prefer less frequent


class PromptRequest(BaseModel):
    prompt: str
    confirm: bool = False
    plan_id: Optional[str] = None
    session_id: str = "default"
    fs_scope: Optional[str] = None


@router.post("/run")
async def run_prompt(request: PromptRequest) -> Dict[str, Any]:
    """Two-phase agent endpoint with memory.

    Phase 1 (confirm=false, default):
        Analyze the prompt (with chat history + long-term memories) → return
        either a conversational response or a plan for the user to review.

    Phase 2 (confirm=true, plan_id provided):
        Execute the confirmed plan steps sequentially, then update memory.
    """
    session_id = request.session_id

    # --- Phase 2: execute a confirmed plan ---
    if request.confirm and request.plan_id:
        steps = _plan_cache.pop(request.plan_id, None)
        if steps is None:
            raise HTTPException(status_code=404, detail="Plan not found or already executed. Please send a new request.")
        outcome = await _execute_plan(steps, prompt=request.prompt, fs_scope=request.fs_scope)
        chat_memory.add(session_id, "user", f"[confirmed plan] {request.prompt}")
        chat_memory.add(
            session_id, "assistant",
            f"[executed plan: {outcome['completed']}/{outcome['total_steps']} steps succeeded]",
        )
        outcome["memories_learned"] = await _learn_from_turn(
            request.prompt,
            f"Plan of {outcome['total_steps']} steps executed, "
            f"{outcome['completed']} succeeded. Tools used: "
            + ", ".join(r["tool"] for r in outcome["results"]),
            force=True,  # always extract after plan execution — highest signal
        )
        return outcome

    # --- Phase 1: analyze and plan ---
    if request.confirm and not request.plan_id:
        raise HTTPException(status_code=400, detail="confirm=true requires a plan_id.")

    adapter = _get_adapter()
    memories = long_term_memory.all()

    # JarvisBrainManager uses agy --conversation which carries its own multi-turn
    # context natively — injecting ChatMemory history on top doubles token cost for
    # no benefit.  Only fetch + pass history for the Groq fallback adapter path.
    from app.modules.antigravity.brain import JarvisBrainManager
    if isinstance(adapter, JarvisBrainManager):
        history = []  # agy session is the short-term memory
    else:
        history = chat_memory.history(session_id)

    try:
        analysis = await adapter.analyze_prompt(request.prompt, history=history, memories=memories)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM communication failed: {exc}")

    chat_memory.add(session_id, "user", request.prompt)

    if analysis["type"] == "response":
        message = analysis["message"]
        chat_memory.add(session_id, "assistant", message)
        return {
            "mode": "response",
            "message": message,
            "memories_learned": await _learn_from_turn(request.prompt, f"Agent replied: {message}"),
        }

    if analysis["type"] == "clarify":
        message = analysis["message"]
        chat_memory.add(session_id, "assistant", f"[clarify] {message}")
        return {
            "mode": "clarify",
            "message": message,
            "context": analysis.get("context", {}),
        }

    # analysis["type"] == "plan"
    plan_id = analysis["plan_id"]
    _plan_cache[plan_id] = analysis["steps"]
    step_summaries = "; ".join(f"{i + 1}. {s['description']}" for i, s in enumerate(analysis["steps"]))
    chat_memory.add(session_id, "assistant", f"[proposed plan] {step_summaries}")
    return {
        "mode": "plan",
        "plan_id": plan_id,
        "reasoning": analysis.get("reasoning", ""),
        "steps": [
            {"index": i, "tool": s["tool"], "description": s["description"], "params": s["params"]}
            for i, s in enumerate(analysis["steps"])
        ],
        "message": "Please review the plan above and confirm to execute.",
    }


async def _learn_from_turn(prompt: str, outcome: str, force: bool = False) -> List[str]:
    """Extract durable facts from a turn and store them (best-effort).

    Extraction is throttled to every MEMORY_EXTRACTION_INTERVAL conversational
    turns to avoid paying the ~20s agy overhead on every message.  Pass
    ``force=True`` to bypass the counter (used after plan confirmations, which
    carry the most signal).
    """
    global _turn_counter
    _turn_counter += 1

    if not force and (_turn_counter % MEMORY_EXTRACTION_INTERVAL != 0):
        return []  # skip this turn

    try:
        facts = await _get_adapter().extract_memories(prompt, outcome)
    except Exception as exc:
        logger.warning("Memory extraction failed: %s", exc)
        return []
    learned = [f for f in facts if long_term_memory.add(f)]
    if learned:
        logger.info("Learned %d new long-term memories", len(learned))
    return learned


async def _execute_plan(steps: List[Dict[str, Any]], prompt: str = "", fs_scope: Optional[str] = None) -> Dict[str, Any]:
    """Execute plan steps sequentially and return collected results."""
    results: List[Dict[str, Any]] = []
    for i, step in enumerate(steps):
        tool_name = step["tool"]
        params = step["params"]
        description = step.get("description", tool_name)

        if tool_name == "fork":
            # Pseudo-tool: not in the registry — fork a background worker.
            result = await _fork_task(params, prompt, fs_scope=fs_scope)
            session_id = result.get("data", {}).get("session_id") if result.get("data") else None
            results.append({
                "index": i,
                "tool": tool_name,
                "description": description,
                "success": result["success"],
                "data": result["data"],
                "error": result.get("error"),
            })

            # If there are subsequent dependent steps, chain them as a sequential reactive pipeline
            if result["success"] and session_id and (i + 1 < len(steps)):
                from app.core.events.orchestrator import get_orchestrator
                orch = get_orchestrator()
                next_step = steps[i + 1]
                remaining_downstream = steps[i + 2:] if (i + 2 < len(steps)) else []
                hook = orch.register_hook(
                    target_session_id=session_id,
                    action_tool=next_step["tool"],
                    action_params=next_step.get("params", {}),
                    description=next_step.get("description", ""),
                    downstream_steps=remaining_downstream,
                )
                for pending_step in steps[i + 1:]:
                    results.append({
                        "index": len(results),
                        "tool": pending_step["tool"],
                        "description": f"[Chained] {pending_step.get('description', pending_step['tool'])}",
                        "success": True,
                        "data": {"status": "chained", "hook_id": hook.id, "target_session": session_id},
                    })
                # Break because remaining pipeline is now handled asynchronously by the event orchestrator
                break
            continue

        try:
            result = await engine.run(tool_name, params)
            results.append({
                "index": i,
                "tool": tool_name,
                "description": description,
                "success": result.success,
                "data": result.data,
                "error": result.error,
            })
            logger.info("Plan step %d/%d succeeded: %s", i + 1, len(steps), tool_name)
        except Exception as exc:
            results.append({
                "index": i,
                "tool": tool_name,
                "description": description,
                "success": False,
                "data": None,
                "error": {"code": "EXECUTION_ERROR", "message": str(exc)},
            })
            logger.warning("Plan step %d/%d failed: %s — %s", i + 1, len(steps), tool_name, exc)

    all_ok = all(r["success"] for r in results)
    return {
        "mode": "execution",
        "success": all_ok,
        "total_steps": len(steps),
        "completed": sum(1 for r in results if r["success"]),
        "results": results,
    }


# Default toolset for a forked OpenCode worker when the LLM/user didn't specify one.
_DEFAULT_FORK_TOOLS = [
    "list_directory", "read_file", "write_file", "create_file",
    "create_folder", "exists", "search_content", "search_files",
]


async def _fork_task(params: Dict[str, Any], prompt: str, fs_scope: Optional[str] = None) -> Dict[str, Any]:
    """Fork a background worker session via the workers module and record a tracked Task in SQLite."""
    import os
    from app.api.routes import workers as workers_routes
    from app.workers.base.contract import TaskContract

    objective = (params.get("objective") or "").strip() or prompt.strip() or "Forked task"
    
    # Dynamic workspace scope resolution:
    # Priority: params['fs_scope'] -> explicit request fs_scope -> directory mentioned in prompt -> JARVIS_WORKSPACE env var -> 'D:/workspace'
    import re
    default_scope = os.getenv("JARVIS_WORKSPACE", "D:/workspace")
    explicit_scope = (params.get("fs_scope") or "").strip() or (fs_scope or "").strip()
    if not explicit_scope:
        path_match = re.search(r"(?:in|to|inside|folder|directory|at)\s+['\"]?([A-Za-z]:[\\/][\w\-\.\s\\/]+|\.[\w\-\.\s\\/]+)['\"]?", prompt, re.IGNORECASE)
        if path_match:
            explicit_scope = path_match.group(1).strip()

    fs_scope_val = explicit_scope or default_scope
    try:
        os.makedirs(fs_scope_val, exist_ok=True)
    except Exception:
        pass
    allowed = params.get("allowed_tools") or list(_DEFAULT_FORK_TOOLS)

    reqs = params.get("requirements") or []
    if isinstance(reqs, str):
        reqs = [reqs.strip()]
    cons = params.get("constraints") or []
    if isinstance(cons, str):
        cons = [cons.strip()]
    crit = params.get("success_criteria") or []
    if isinstance(crit, str):
        crit = [crit.strip()]

    # 1. Create a tracked Task record in SQLite database
    db_task_id = None
    try:
        from app.modules.database.db import SessionLocal
        from app.modules.database.repository import Repository
        with SessionLocal() as db:
            repo = Repository(db)
            db_task = repo.create_task(name=objective, status="running")
            db_task_id = db_task.id
    except Exception as exc:
        logger.warning("Could not persist Task to database: %s", exc)

    prior_handover = params.get("prior_handover")
    is_refinement = bool(params.get("is_refinement", False))

    try:
        contract = TaskContract(
            objective=objective,
            requirements=reqs,
            constraints=cons,
            success_criteria=crit,
            fs_scope=fs_scope_val,
            allowed_tools=allowed,
            max_steps=int(params.get("max_steps", 20)),
            master_prompt=params.get("master_prompt"),
            model=params.get("model"),
            prior_handover=prior_handover,
            is_refinement=is_refinement,
        )
    except Exception as exc:
        if db_task_id:
            try:
                with SessionLocal() as db:
                    Repository(db).update_task_status(db_task_id, "failed")
            except Exception:
                pass
        return {"success": False, "data": None, "error": {"code": "INVALID_CONTRACT", "message": str(exc)}}

    try:
        state = await workers_routes.launch_worker(
            contract, worker_type=params.get("worker_type", "antigravity_worker")
        )
    except Exception as exc:
        if db_task_id:
            try:
                with SessionLocal() as db:
                    Repository(db).update_task_status(db_task_id, "failed")
            except Exception:
                pass
        return {"success": False, "data": None, "error": {"code": "FORK_FAILED", "message": str(exc)}}

    session_id = state["session_id"]
    return {
        "success": True,
        "data": {
            "task_id": db_task_id,
            "session_id": session_id,
            "status": state.get("status"),
            "worker_url": f"/worker/{session_id}",
            "stream_url": f"/workers/{session_id}/stream",
            "message": f"Task #{db_task_id or session_id} forked — open /workers/{session_id}/stream to watch live.",
        },
    }


@router.get("/memory")
async def get_memory() -> Dict[str, Any]:
    """List stored long-term memories (most recent first)."""
    return {"memories": long_term_memory.all(limit=50)}


@router.delete("/memory")
async def clear_memory() -> Dict[str, Any]:
    """Clear all long-term memories."""
    return {"deleted": long_term_memory.clear()}


@router.get("/history")
async def get_history(session_id: str = "default") -> Dict[str, Any]:
    """View the short-term chat history for a session."""
    return {"session_id": session_id, "history": chat_memory.history(session_id)}


@router.delete("/history")
async def clear_history(session_id: str = "default") -> Dict[str, Any]:
    """Clear short-term history for a session (or all sessions with session_id=all)."""
    sid = None if session_id == "all" else session_id
    chat_memory.clear(sid)
    return {"cleared": session_id}
