import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.workers.antigravity_worker.agent.cli_client import PersistentAgyDaemon, RunResult


@pytest.mark.asyncio
async def test_persistent_daemon_ensure_running():
    daemon = PersistentAgyDaemon(session_id="test-daemon-ses")
    
    with patch("app.workers.antigravity_worker.agent.config.get_agy_binary", return_value="C:/bin/agy.exe"), \
         patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_subproc:
        
        mock_proc = MagicMock()
        mock_proc.returncode = None
        mock_subproc.return_value = mock_proc

        started = await daemon.ensure_running()
        assert started is True
        assert daemon.proc == mock_proc
        assert mock_subproc.called


@pytest.mark.asyncio
async def test_persistent_daemon_send_turn_success():
    daemon = PersistentAgyDaemon(session_id="test-daemon-ses")
    daemon.proc = MagicMock()
    daemon.proc.returncode = None
    daemon.proc.stdin = MagicMock()
    daemon.proc.stdin.drain = AsyncMock()
    daemon.proc.stdout = AsyncMock()

    # Simulate verified NDJSON stdout line
    daemon.proc.stdout.readline.side_effect = [
        b'{"event": "step_update", "step_update": {"text_delta": "Hello from warm daemon"}}\n',
        b'{"event": "result", "result": {"status": "SUCCESS", "response": "Hello from warm daemon"}}\n',
        b'',
    ]

    with patch.object(daemon, "ensure_running", return_value=True):
        res = await daemon.send_turn("Hi Jarvis")
        assert res.success is True
        assert "Hello from warm daemon" in res.output_text
        assert res.session_id == "test-daemon-ses"


@pytest.mark.asyncio
async def test_persistent_daemon_stop():
    daemon = PersistentAgyDaemon(session_id="test-daemon-ses")
    mock_proc = MagicMock()
    mock_proc.stdin = MagicMock()
    mock_proc.terminate = MagicMock()
    mock_proc.wait = AsyncMock()
    daemon.proc = mock_proc

    await daemon.stop()
    assert daemon.proc is None
    assert mock_proc.terminate.called
