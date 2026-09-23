import asyncio
import json
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_frontend_backend_integration_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check (Frontend Header)
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

        # 2. List workers (Frontend /workers page)
        res = await client.get("/workers/list")
        assert res.status_code == 200
        assert "workers" in res.json()

        # 3. Fork worker (Frontend /workers ForkForm)
        fork_payload = {
            "objective": "Inspect project directory and test file reading",
            "worker_type": "opencode_worker",
            "fs_scope": "D:/Ai automation backend",
            "allowed_tools": ["list_directory", "read_file", "exists"],
            "max_steps": 5,
        }
        res = await client.post("/workers/fork", json=fork_payload)
        assert res.status_code == 200
        data = res.json()
        assert "session_id" in data
        session_id = data["session_id"]
        assert data["status"] in ("running", "completed", "idle")

        # 4. Get worker detail (Frontend /worker/[id] page)
        res = await client.get(f"/workers/{session_id}")
        assert res.status_code == 200
        state = res.json()
        assert state["session_id"] == session_id
        assert state["objective"] == fork_payload["objective"]

        # 5. Get worker artifacts (Frontend /worker/[id] artifacts panel)
        res = await client.get(f"/workers/{session_id}/artifacts")
        assert res.status_code == 200
        assert "artifacts" in res.json()

        # 6. Worker intervention (Frontend /worker/[id] intervention panel)
        res = await client.post(f"/workers/{session_id}/intervene", json={"message": "Speed up execution"})
        assert res.status_code == 200
        assert res.json()["status"] == "intervention recorded"

        # 7. Worker cancellation (Frontend /worker/[id] cancel button)
        res = await client.post(f"/workers/{session_id}/cancel")
        assert res.status_code == 200
        assert res.json()["status"] == "cancellation requested"
        await asyncio.sleep(0.05)

        # 8. Chat history clear (Frontend 'New Chat' button)
        res = await client.delete("/agent/history?session_id=default")
        assert res.status_code == 200
        assert res.json()["cleared"] == "default"
