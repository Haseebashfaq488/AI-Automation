import pytest
from app.workers.antigravity_worker.agent.milestones import build_master_task_prompt
from app.modules.antigravity.brain import JarvisBrainManager


def test_build_master_task_prompt_structure():
    prompt = build_master_task_prompt(
        objective="Create a high-speed data parser",
        fs_scope="D:/workspace/parser",
        requirements=["Parse CSV and JSON", "Handle 100k rows/sec"],
        constraints=["Do not use external heavy libraries"],
        success_criteria=["Unit tests pass", "Benchmark meets 100k rows/sec"],
    )

    assert "# 🎯 MASTER TASK SPECIFICATION" in prompt
    assert "Create a high-speed data parser" in prompt
    assert "D:/workspace/parser" in prompt
    assert "Parse CSV and JSON" in prompt
    assert "Do not use external heavy libraries" in prompt
    assert "Mandatory Engineering Execution Protocol" in prompt
    assert "Unit Testing" in prompt
    assert "Dataflow & Pipeline Testing" in prompt
    assert "Mandatory Final Summary Format" in prompt


def test_brain_manager_generate_specification():
    brain = JarvisBrainManager()
    spec = brain.generate_worker_task_specification(
        objective="Implement authentication gateway",
        fs_scope="D:/workspace/auth",
    )
    assert "# 🎯 MASTER TASK SPECIFICATION" in spec
    assert "Implement authentication gateway" in spec
    assert "D:/workspace/auth" in spec
    assert "Mandatory Testing Protocol" in spec


def test_brain_manager_evaluate_completion():
    brain = JarvisBrainManager()
    
    # Successful result
    res_ok = {
        "success": True,
        "completed_steps": 3,
        "tools_used": ["write_file", "run_command", "run_command"],
        "summary": "All tests passed successfully.",
    }
    evaluation = brain.evaluate_worker_completion(
        session_id="test_worker_123",
        contract={"objective": "Build parser"},
        result=res_ok,
    )
    assert evaluation["verdict"] == "RESOLVED"
    assert evaluation["success"] is True
    assert "Build parser" in evaluation["headline"]

    # Blocked result
    res_err = {
        "success": False,
        "completed_steps": 1,
        "errors": [{"message": "SyntaxError in test file"}],
    }
    eval_err = brain.evaluate_worker_completion(
        session_id="test_worker_123",
        contract={"objective": "Build parser"},
        result=res_err,
    )
    assert eval_err["verdict"] == "BLOCKED"
    assert eval_err["success"] is False
