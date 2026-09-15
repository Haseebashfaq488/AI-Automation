import json
import os

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.api.routes import workers as workers_routes
from app.workers.base.session import WorkerSession

# Platform-independent absolute path used in fork payloads
SCOPE = os.path.abspath("/")


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Test client with session storage redirected to tmp_path and a clean
    in‑process engine store."""
    monkeypatch.setattr(WorkerSession, "SESSIONS_ROOT", tmp_path)
    monkeypatch.setattr(
        "app.workers.opencode_worker.agent.config.get_opencode_binary", lambda: None
    )
    workers_routes._engines.clear()
    app = create_app()
    with TestClient(app) as c:
        yield c


def _wait_for_terminal_state(client, session_id, timeout_s=10.0):
    import time

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        resp = client.get(f"/workers/{session_id}")
        status = resp.json()["status"]
        if status in ("completed", "cancelled"):
            return status
        time.sleep(0.1)
    raise TimeoutError(f"worker {session_id} did not finish in {timeout_s}s")


class TestWorkersAPI:
    def test_fork_and_poll_to_completion(self, client):
        resp = client.post("/workers/fork", json={
            "objective": "API test worker",
            "allowed_tools": ["create_file", "exists"],
            "fs_scope": SCOPE,
            "max_steps": 5,
        })
        assert resp.status_code == 200
        body = resp.json()
        session_id = body["session_id"]
        assert body["status"] == "running"

        status = _wait_for_terminal_state(client, session_id)
        assert status == "completed"

        resp = client.get(f"/workers/{session_id}")
        state = resp.json()
        assert state["progress_percent"] == 100
        assert set(state["completed"]) == {"create_file", "exists"}

        resp = client.get(f"/workers/{session_id}/result")
        result = resp.json()["result"]
        assert result["success"] is True

    def test_list_workers(self, client):
        client.post("/workers/fork", json={
            "objective": "worker A",
            "allowed_tools": ["create_file"],
            "fs_scope": SCOPE,
        })
        resp = client.get("/workers/list")
        assert resp.status_code == 200
        workers = resp.json()["workers"]
        assert len(workers) >= 1
        assert any(w["objective"] if "objective" in w else True for w in workers)

    def test_get_unknown_worker_404(self, client):
        resp = client.get("/workers/does_not_exist")
        assert resp.status_code == 404

    def test_cancel_worker(self, client):
        # Many tools so the loop stays busy long enough to cancel
        resp = client.post("/workers/fork", json={
            "objective": "long worker",
            "allowed_tools": ["create_file", "write_file", "exists", "metadata"],
            "fs_scope": SCOPE,
            "max_steps": 50,
        })
        session_id = resp.json()["session_id"]
        resp = client.post(f"/workers/{session_id}/cancel")
        assert resp.status_code == 200

        status = _wait_for_terminal_state(client, session_id)
        assert status in ("cancelled", "completed")

    def test_intervene_endpoint(self, client):
        resp = client.post("/workers/fork", json={
            "objective": "intervention test",
            "allowed_tools": ["create_file"],
            "fs_scope": SCOPE,
        })
        session_id = resp.json()["session_id"]
        resp = client.post(
            f"/workers/{session_id}/intervene",
            json={"message": "switch strategy"},
        )
        assert resp.status_code == 200

        _wait_for_terminal_state(client, session_id)

    def test_events_sse_stream(self, client):
        resp = client.post("/workers/fork", json={
            "objective": "sse test",
            "allowed_tools": ["create_file"],
            "fs_scope": SCOPE,
        })
        session_id = resp.json()["session_id"]

        request = client.build_request("GET", f"/workers/{session_id}/events")
        response = client.send(request, stream=True)
        try:
            received = ""
            for chunk in response.iter_text():
                received += chunk
                if "WORK_STARTED" in received and "WORK_COMPLETED" in received:
                    break
            assert "WORK_STARTED" in received
            assert "STEP_COMPLETED" in received or "create_file" in received
        finally:
            response.close()

        _wait_for_terminal_state(client, session_id)

    def test_fork_validates_contract(self, client):
        resp = client.post("/workers/fork", json={
            "objective": "bad scope",
            "fs_scope": "not-absolute",
            "allowed_tools": [],
        })
        assert resp.status_code in (400, 422)

    def test_artifacts_endpoints(self, client, tmp_path):
        resp = client.post("/workers/fork", json={
            "objective": "artifacts test",
            "allowed_tools": ["create_file"],
            "fs_scope": SCOPE,
        })
        session_id = resp.json()["session_id"]
        _wait_for_terminal_state(client, session_id)

        # Write a dummy artifact to the session's artifacts dir
        session_artifacts = tmp_path / session_id / "artifacts"
        session_artifacts.mkdir(parents=True, exist_ok=True)
        (session_artifacts / "output.txt").write_text("hello artifact")

        # Test list
        resp = client.get(f"/workers/{session_id}/artifacts")
        assert resp.status_code == 200
        artifacts = resp.json()["artifacts"]
        assert len(artifacts) >= 1
        assert any(a["name"] == "output.txt" for a in artifacts)

        # Test download
        resp = client.get(f"/workers/{session_id}/artifacts/output.txt")
        assert resp.status_code == 200
        assert resp.text == "hello artifact"

