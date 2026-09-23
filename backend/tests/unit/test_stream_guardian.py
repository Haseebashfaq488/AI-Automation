import os
import pytest
from app.workers.base.contract import TaskContract
from app.workers.base.guardian import ActiveStreamGuardian


def test_guardian_boundary_violation_detection():
    contract = TaskContract(
        objective="Test boundary safety",
        fs_scope="D:/workspace",
    )
    guardian = ActiveStreamGuardian(contract, session_id="test_sess_01")

    # In-scope path
    intervention = guardian.inspect_event(
        "STEP_COMPLETED",
        {"tool": "write_file", "path": "D:/workspace/test.txt", "success": True}
    )
    assert intervention is None
    assert len(guardian.violations) == 0

    # Out-of-scope path
    intervention_out = guardian.inspect_event(
        "STEP_COMPLETED",
        {"tool": "write_file", "path": "C:/Windows/System32/evil.dll", "success": True}
    )
    assert intervention_out is not None
    assert "Boundary violation detected" in intervention_out
    assert len(guardian.violations) == 1
    assert guardian.violations[0]["type"] == "boundary_violation"


def test_guardian_stagnation_loop_detection():
    contract = TaskContract(
        objective="Test stagnation safety",
        fs_scope="D:/workspace",
    )
    guardian = ActiveStreamGuardian(contract, session_id="test_sess_02")

    # 1st failure
    interv1 = guardian.inspect_event(
        "STEP_FAILED",
        {"tool": "run_command", "cmd": "pytest tests/", "error": "SyntaxError", "success": False}
    )
    assert interv1 is None

    # 2nd failure (same signature)
    interv2 = guardian.inspect_event(
        "STEP_FAILED",
        {"tool": "run_command", "cmd": "pytest tests/", "error": "SyntaxError", "success": False}
    )
    assert interv2 is None

    # 3rd failure triggers intervention
    interv3 = guardian.inspect_event(
        "STEP_FAILED",
        {"tool": "run_command", "cmd": "pytest tests/", "error": "SyntaxError", "success": False}
    )
    assert interv3 is not None
    assert "Stagnation detected" in interv3
    assert len(guardian.violations) == 1
    assert guardian.violations[0]["type"] == "stagnation_loop"


def test_guardian_testing_progress_tracking():
    contract = TaskContract(
        objective="Test progress tracking",
        fs_scope="D:/workspace",
    )
    guardian = ActiveStreamGuardian(contract, session_id="test_sess_03")

    assert not guardian.unit_tests_detected
    assert not guardian.dataflow_tests_detected

    guardian.inspect_event(
        "STEP_COMPLETED",
        {"tool": "run_command", "cmd": "pytest test_units.py", "success": True}
    )
    assert guardian.unit_tests_detected

    guardian.inspect_event(
        "STEP_COMPLETED",
        {"tool": "run_command", "cmd": "python run_dataflow_test.py", "success": True}
    )
    assert guardian.dataflow_tests_detected

    status = guardian.get_status()
    assert status["unit_tests_detected"] is True
    assert status["dataflow_tests_detected"] is True
