import json
from pathlib import Path
from typing import Optional

from app.workers.base.contract import TaskContract


class WorkerSession:
    """Manages a single worker's on-disk session state.

    On fork, creates the following structure under
    ``backend/worker_sessions/<session_id>/``:

    task.json       → TaskContract as JSON
    state.json      → Current progress (step, completed, remaining, errors)
    events.jsonl    → Append-only log of step events
    artifacts/      → Files created/modified by the worker
    logs/           → Human-readable execution logs
    result.json     → Final result (written on WORK_COMPLETED or intervention)
    """

    # Root directory for all worker sessions
    SESSIONS_ROOT = Path(__file__).resolve().parents[3] / "worker_sessions"

    def __init__(self, session_id: str, contract: "Optional[TaskContract]" = None):
        self.session_id = session_id
        self.contract = contract
        self.path = self.SESSIONS_ROOT / session_id
        self.path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Initialise a fresh session from a contract
    # ------------------------------------------------------------------
    def fork(self) -> "WorkerSession":
        """Create the session directory and write the initial contract.

        Returns self for convenience.
        """
        # Write task.json
        task_path = self.path / "task.json"
        task_path.write_text(self.contract.model_dump_json(), encoding="utf-8")

        # Write state.json (initial state)
        state_path = self.path / "state.json"
        state_path.write_text(
            json.dumps(
                {
                    "current_step": None,
                    "completed": [],
                    "remaining": [str(self.contract.objective)],
                    "errors": [],
                    "progress_percent": 0,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        # Initialise empty artefacts & logs dirs
        (self.path / "artifacts").mkdir(parents=True, exist_ok=True)
        (self.path / "logs").mkdir(parents=True, exist_ok=True)

        # Empty events.jsonl
        (self.path / "events.jsonl").write_text("", encoding="utf-8")

        # Empty result.json (will be written on completion)
        (self.path / "result.json").write_text("{}", encoding="utf-8")

        return self

    # -----------------------------------------------------------------
    # Read/write helpers
    # -----------------------------------------------------------------
    def read_task(self) -> "TaskContract":
        data = json.loads((self.path / "task.json").read_text(encoding="utf-8"))
        return TaskContract.model_validate(data)

    def write_task(self, contract: "TaskContract") -> None:
        (self.path / "task.json").write_text(contract.model_dump_json(), encoding="utf-8")

    def read_state(self) -> dict:
        state_path = self.path / "state.json"
        if not state_path.exists():
            return {
                "current_step": None,
                "completed": [],
                "remaining": [],
                "errors": [],
                "progress_percent": 0,
            }
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {
                "current_step": None,
                "completed": [],
                "remaining": [],
                "errors": [],
                "progress_percent": 0,
            }

    def write_state(self, state: dict) -> None:
        (self.path / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

    def append_event(self, event_type: str, data: dict) -> None:
        """Append a single JSON line to events.jsonl."""
        line = json.dumps({"type": event_type, "data": data, "step": data.get("step")})
        with open(self.path / "events.jsonl", "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def read_result(self) -> dict:
        try:
            return json.loads((self.path / "result.json").read_text(encoding="utf-8"))
        except Exception:
            return {}

    def write_result(self, result: dict) -> None:
        (self.path / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    def read_plan(self) -> str:
        plan_path = self.path / "plan.md"
        if plan_path.exists():
            try:
                return plan_path.read_text(encoding="utf-8")
            except Exception:
                pass
        return ""

    def write_plan(self, plan_text: str) -> None:
        (self.path / "plan.md").write_text(plan_text, encoding="utf-8")

    def read_test_results(self) -> dict:
        results_path = self.path / "test_results.json"
        if results_path.exists():
            try:
                return json.loads(results_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def write_test_results(self, results: dict) -> None:
        (self.path / "test_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    @property
    def completed(self) -> list:
        return self.read_state().get("completed", [])

    @property
    def remaining(self) -> list:
        return self.read_state().get("remaining", [])

    @property
    def errors(self) -> list:
        return self.read_state().get("errors", [])

    @property
    def progress_percent(self) -> int:
        return self.read_state().get("progress_percent", 0)

    @property
    def current_step(self) -> Optional[str]:
        return self.read_state().get("current_step")

    @property
    def session_dir(self) -> Path:
        return self.path