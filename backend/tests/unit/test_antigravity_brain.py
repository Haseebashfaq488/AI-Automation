"""Unit tests for JarvisBrainManager and living memory system."""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.modules.antigravity.brain import JarvisBrainManager, get_brain_manager
from app.workers.antigravity_worker.agent.cli_client import RunResult


@pytest.fixture
def temp_memory_file(tmp_path: Path) -> Path:
    mem_file = tmp_path / "JARVIS_MEMORY.md"
    mem_file.write_text(
        "# 🧠 JARVIS LIVING MEMORY\n\n"
        "## 👤 User Profile\n- Owner: Haseeb\n- Phone: +923098956995\n\n"
        "## 📝 Scratchpad & Temporary Notes\n- [2026-09-16 22:00] Initial note\n",
        encoding="utf-8",
    )
    return mem_file


def test_brain_manager_reads_memory(temp_memory_file: Path):
    manager = JarvisBrainManager(memory_path=temp_memory_file)
    content = manager.read_memory()
    assert "Haseeb" in content
    assert "+923098956995" in content


def test_brain_manager_appends_scratchpad(temp_memory_file: Path):
    manager = JarvisBrainManager(memory_path=temp_memory_file)
    success = manager.append_scratchpad("Remember favorite color is navy blue")
    assert success is True

    updated = manager.read_memory()
    assert "favorite color is navy blue" in updated


def test_brain_manager_validates_plan_steps(temp_memory_file: Path):
    manager = JarvisBrainManager(memory_path=temp_memory_file)

    raw_steps = [
        {"tool": "send_message", "params": {"to": "+923098956995", "message": "Hello!"}},
        {"tool": "unknown_tool", "params": {"foo": "bar"}},
        {"tool": "send_email", "params": {"to": "user@example.com", "body": "test"}},
    ]

    valid, dropped = manager._validate_plan_steps(raw_steps)
    assert len(valid) == 2
    assert len(dropped) == 1
    assert dropped[0]["tool"] == "unknown_tool"
    assert valid[0]["tool"] == "send_message"
    assert valid[1]["tool"] == "send_email"


@pytest.mark.asyncio
async def test_brain_manager_analyze_prompt_conversational(temp_memory_file: Path):
    manager = JarvisBrainManager(memory_path=temp_memory_file)

    mock_run_result = RunResult(
        success=True,
        output_text='{"type": "response", "message": "Hello Haseeb! How can I help you today?"}',
    )

    with patch("app.modules.antigravity.brain.run_antigravity_cli", new_callable=AsyncMock) as mock_cli:
        mock_cli.return_value = mock_run_result
        result = await manager.analyze_prompt("Hi Jarvis")

        assert result["type"] == "response"
        assert "Hello Haseeb!" in result["message"]


@pytest.mark.asyncio
async def test_brain_manager_analyze_prompt_plan(temp_memory_file: Path):
    manager = JarvisBrainManager(memory_path=temp_memory_file)

    mock_run_result = RunResult(
        success=True,
        output_text=(
            '{"type": "plan", "reasoning": "Send WhatsApp message", '
            '"steps": [{"tool": "send_message", "params": {"to": "+923098956995", "message": "Test"}'
            ', "description": "Send text message"}]}'
        ),
    )

    with patch("app.modules.antigravity.brain.run_antigravity_cli", new_callable=AsyncMock) as mock_cli:
        mock_cli.return_value = mock_run_result
        result = await manager.analyze_prompt("Send message to Haseeb saying Test")

        assert result["type"] == "plan"
        assert len(result["steps"]) == 1
        assert result["steps"][0]["tool"] == "send_message"
        assert "plan_id" in result


@pytest.mark.asyncio
async def test_brain_manager_auto_records_explicit_remember(temp_memory_file: Path):
    manager = JarvisBrainManager(memory_path=temp_memory_file)

    mock_run_result = RunResult(
        success=True,
        output_text='{"type": "response", "message": "I will remember that your car is a Tesla."}',
    )

    with patch("app.modules.antigravity.brain.run_antigravity_cli", new_callable=AsyncMock) as mock_cli:
        mock_cli.return_value = mock_run_result
        await manager.analyze_prompt("Remember that my car is a Tesla")

        content = manager.read_memory()
        assert "my car is a Tesla" in content


@pytest.mark.asyncio
async def test_brain_manager_worker_intent_fork(temp_memory_file: Path):
    manager = JarvisBrainManager(memory_path=temp_memory_file)

    # 1. Direct worker command
    result1 = await manager.analyze_prompt("make a worker do this task: build a calculator app")
    assert result1["type"] == "plan"
    assert result1["steps"][0]["tool"] == "fork"
    assert "calculator app" in result1["steps"][0]["params"]["objective"]

    # 2. Delegate task command
    result2 = await manager.analyze_prompt("delegate a task: refactor user authentication")
    assert result2["type"] == "plan"
    assert result2["steps"][0]["tool"] == "fork"
    assert "refactor user authentication" in result2["steps"][0]["params"]["objective"]

    # 3. Contextual worker task from history
    history = [
        {"role": "user", "content": "Compile the financial report document and export to PDF"},
        {"role": "assistant", "content": "I can help with that."},
    ]
    result3 = await manager.analyze_prompt("make a worker do this exact task", history=history)
    assert result3["type"] == "plan"
    assert result3["steps"][0]["tool"] == "fork"
    assert "financial report" in result3["steps"][0]["params"]["objective"]

