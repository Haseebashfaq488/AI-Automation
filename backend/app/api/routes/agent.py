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


class PromptRequest(BaseModel):
    prompt: str
    confirm: bool = False
    plan_id: Optional[str] = None
    session_id: str = "default"


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
        outcome = await _execute_plan(steps, prompt=request.prompt)
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
        )
        return outcome

    # --- Phase 1: analyze and plan ---
    if request.confirm and not request.plan_id:
        raise HTTPException(status_code=400, detail="confirm=true requires a plan_id.")

    adapter = _get_adapter()
    history = chat_memory.history(session_id)
    memories = long_term_memory.all()

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


async def _learn_from_turn(prompt: str, outcome: str) -> List[str]:
    """Extract durable facts from a turn and store them (best-effort)."""
    try:
        facts = await _get_adapter().extract_memories(prompt, outcome)
    except Exception as exc:
        logger.warning("Memory extraction failed: %s", exc)
        return []
    learned = [f for f in facts if long_term_memory.add(f)]
    if learned:
        logger.info("Learned %d new long-term memories", len(learned))
    return learned


async def _execute_plan(steps: List[Dict[str, Any]], prompt: str = "") -> Dict[str, Any]:
    """Execute plan steps sequentially and return collected results."""
    results: List[Dict[str, Any]] = []
    for i, step in enumerate(steps):
        tool_name = step["tool"]
        params = step["params"]
        description = step.get("description", tool_name)

        if tool_name == "fork":
            # Pseudo-tool: not in the registry — fork a background worker.
            result = await _fork_task(params, prompt)
            results.append({
                "index": i,
                "tool": tool_name,
                "description": description,
                "success": result["success"],
                "data": result["data"],
                "error": result.get("error"),
            })
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


async def _fork_task(params: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    """Fork a background worker session via the workers module.

    `fork` is a pseudo-tool: the LLM plans it like any other tool, but it is
    executed here against the worker engine store instead of the tool registry.
    """
    import os
    from app.api.routes import workers as workers_routes
    from app.workers.base.contract import TaskContract

    objective = (params.get("objective") or "").strip() or prompt.strip() or "Forked task"
    fs_scope = params.get("fs_scope") or os.path.abspath(os.sep)
    allowed = params.get("allowed_tools") or list(_DEFAULT_FORK_TOOLS)

    try:
        contract = TaskContract(
            objective=objective,
            requirements=params.get("requirements", []),
            constraints=params.get("constraints", []),
            success_criteria=params.get("success_criteria", []),
            fs_scope=fs_scope,
            allowed_tools=allowed,
            max_steps=int(params.get("max_steps", 20)),
            master_prompt=params.get("master_prompt"),
            model=params.get("model"),
        )
    except Exception as exc:
        return {"success": False, "data": None, "error": {"code": "INVALID_CONTRACT", "message": str(exc)}}

    try:
        state = await workers_routes.launch_worker(
            contract, worker_type=params.get("worker_type", "antigravity_worker")
        )
    except Exception as exc:
        return {"success": False, "data": None, "error": {"code": "FORK_FAILED", "message": str(exc)}}

    session_id = state["session_id"]
    return {
        "success": True,
        "data": {
            "session_id": session_id,
            "status": state.get("status"),
            "worker_url": f"/worker/{session_id}",
            "message": f"Worker {session_id} forked — open /worker/{session_id} to watch it live.",
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
