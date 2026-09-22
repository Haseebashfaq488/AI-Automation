"""Active Stream Guardian for Worker Supervision.

Monitors real-time worker execution streams, detects path boundary violations,
consecutive command stagnation/loops, and missing testing phases, and triggers
autonomous manager interventions.
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.workers.base.contract import TaskContract

logger = logging.getLogger("jarvis.worker.guardian")


class ActiveStreamGuardian:
    """Supervises a single worker session's real-time event stream."""

    def __init__(self, contract: TaskContract, session_id: str):
        self.contract = contract
        self.session_id = session_id
        self.fs_scope = os.path.abspath(contract.fs_scope)

        # State tracking
        self.consecutive_failures = 0
        self.last_failed_signature: Optional[str] = None
        self.unit_tests_detected = False
        self.dataflow_tests_detected = False
        self.violations: List[Dict[str, Any]] = []
        self.interventions_sent: List[str] = []

    def inspect_event(self, event_type: str, payload: Dict[str, Any]) -> Optional[str]:
        """Inspect a stream event and return an intervention message if deviation is detected."""
        if not getattr(self.contract, "supervisor_enabled", True):
            return None

        # 1. Boundary / Path Scope Check
        path_intervention = self._check_path_scope(event_type, payload)
        if path_intervention:
            self.violations.append({"type": "boundary_violation", "detail": path_intervention})
            self.interventions_sent.append(path_intervention)
            return path_intervention

        # 2. Command Failure & Loop Stagnation Check
        loop_intervention = self._check_stagnation(event_type, payload)
        if loop_intervention:
            self.violations.append({"type": "stagnation_loop", "detail": loop_intervention})
            self.interventions_sent.append(loop_intervention)
            return loop_intervention

        # 3. Track testing progress
        self._track_testing_progress(event_type, payload)

        return None

    def _check_path_scope(self, event_type: str, payload: Dict[str, Any]) -> Optional[str]:
        """Verify that file paths manipulated by the worker remain within fs_scope."""
        target_paths: List[str] = []
        for key in ("path", "source", "destination", "file", "target_dir", "source_dir"):
            val = payload.get(key)
            if isinstance(val, str) and val.strip():
                target_paths.append(val.strip())

        cmd = payload.get("cmd") or payload.get("command") or payload.get("input")
        if isinstance(cmd, str):
            matches = re.findall(r"[A-Za-z]:[/\\][^\s\"']+", cmd)
            target_paths.extend(matches)

        for p in target_paths:
            try:
                abs_p = os.path.abspath(p)
                if not abs_p.lower().startswith(self.fs_scope.lower()):
                    if "site-packages" in abs_p.lower() or "temp" in abs_p.lower() or "appdata" in abs_p.lower():
                        continue
                    return (
                        f"⚠️ Manager Intervention: Boundary violation detected. You attempted to access '{p}', "
                        f"which is outside your assigned workspace scope '{self.fs_scope}'. "
                        f"Refocus your operations strictly inside '{self.fs_scope}'."
                    )
            except Exception:
                pass
        return None

    def _check_stagnation(self, event_type: str, payload: Dict[str, Any]) -> Optional[str]:
        """Detect repeated consecutive failures on the same command/tool."""
        success = payload.get("success")
        is_error = event_type in ("TOOL_ERROR", "ERROR", "STEP_FAILED") or success is False
        error_msg = str(payload.get("error") or payload.get("stderr") or "")

        if is_error:
            tool_or_cmd = str(payload.get("tool") or payload.get("cmd") or payload.get("action") or "unknown")
            signature = f"{tool_or_cmd}:{error_msg[:100]}"
            if signature == self.last_failed_signature:
                self.consecutive_failures += 1
            else:
                self.consecutive_failures = 1
                self.last_failed_signature = signature

            if self.consecutive_failures >= 3:
                self.consecutive_failures = 0
                return (
                    f"⚠️ Manager Intervention: Stagnation detected. You have encountered 3 consecutive failures "
                    f"on '{tool_or_cmd}' (Error: {error_msg[:150]}). "
                    f"Please pause, diagnose the root cause, inspect the error output, and try an alternative approach."
                )
        else:
            if success is True or event_type in ("TOOL_SUCCESS", "STEP_COMPLETED"):
                self.consecutive_failures = 0
                self.last_failed_signature = None

        return None

    def _track_testing_progress(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Identify execution of unit testing and dataflow testing suites."""
        content = json_dump_safe(payload).lower()
        if any(term in content for term in ("pytest", "unittest", "test_", "_test.py", "unit test")):
            self.unit_tests_detected = True
        if any(term in content for term in ("dataflow", "pipeline test", "integration test", "e2e", "end-to-end")):
            self.dataflow_tests_detected = True

    def get_status(self) -> Dict[str, Any]:
        """Return guardian health and observation status."""
        return {
            "session_id": self.session_id,
            "fs_scope": self.fs_scope,
            "unit_tests_detected": self.unit_tests_detected,
            "dataflow_tests_detected": self.dataflow_tests_detected,
            "violations_count": len(self.violations),
            "violations": self.violations,
            "interventions_sent": self.interventions_sent,
        }


def json_dump_safe(obj: Any) -> str:
    """Safe serializer to string for inspection."""
    try:
        return json.dumps(obj)
    except Exception:
        return str(obj)
