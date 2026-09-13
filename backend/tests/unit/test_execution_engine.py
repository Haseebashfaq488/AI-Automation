import pytest
import asyncio
from app.core.execution_engine import ExecutionEngine
from app.registry import registry


@pytest.mark.asyncio
async def test_execution_engine_list_directory():
    engine = ExecutionEngine(registry)
    # Use current directory (project root) which should exist
    result = await engine.run("list_directory", {"path": "."})
    assert result.success is True
    assert result.tool == "list_directory"
    assert "entries" in result.data
    # Ensure at least one entry (the README or other files)
    assert isinstance(result.data["entries"], list)
    # Verify metadata contains duration and risk
    assert "duration_ms" in result.metadata
    assert result.metadata["risk"] == "low"
