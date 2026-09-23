"""Unit tests for system power management endpoints."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_shutdown_endpoint():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        res = client.post("/system/shutdown", json={"delay_seconds": 15, "message": "Test shutdown"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "shutdown_scheduled"
        assert data["delay_seconds"] == 15
        mock_run.assert_called_once()


def test_cancel_shutdown_endpoint():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        res = client.post("/system/cancel-shutdown")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] in ("shutdown_cancelled", "no_shutdown_active")
        mock_run.assert_called_once()


def test_restart_endpoint():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        res = client.post("/system/restart", json={"delay_seconds": 20})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "restart_scheduled"
        assert data["delay_seconds"] == 20


@pytest.mark.asyncio
async def test_shutdown_tool_execution():
    from app.modules.system.tools.shutdown_tool import ShutdownTool
    tool = ShutdownTool()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        res = await tool.execute({"delay_seconds": 10, "message": "Test"})
        assert res["status"] == "shutdown_scheduled"
        assert res["delay_seconds"] == 10
        mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_shutdown_tool_execution():
    from app.modules.system.tools.cancel_shutdown_tool import CancelShutdownTool
    tool = CancelShutdownTool()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        res = await tool.execute({})
        assert res["status"] == "shutdown_cancelled"
        mock_run.assert_called_once()

