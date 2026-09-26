import pytest
import os
from pathlib import Path
from app.core.execution_engine import ExecutionEngine
from app.registry.tool_registry import ToolRegistry
from app.modules.file_management.tools.create_folder import CreateFolderTool
from app.modules.file_management.tools.create_file import CreateFileTool
from app.modules.file_management.tools.write_file import WriteFileTool
from app.modules.file_management.tools.copy import CopyTool
from app.modules.file_management.tools.move import MoveTool
from app.modules.file_management.tools.rename import RenameTool


def get_mutation_engine():
    reg = ToolRegistry()
    reg.register(CreateFolderTool())
    reg.register(CreateFileTool())
    reg.register(WriteFileTool())
    reg.register(CopyTool())
    reg.register(MoveTool())
    reg.register(RenameTool())
    return ExecutionEngine(reg)


@pytest.mark.asyncio
async def test_mutation_tools_flow(tmp_path: Path):
    engine = get_mutation_engine()
    base = tmp_path / "test_dir"
    # 1. create_folder
    result = await engine.run("create_folder", {"path": str(base)})
    assert result.success
    assert base.is_dir()
    # 2. create_file inside folder
    file_path = base / "test.txt"
    result = await engine.run("create_file", {"path": str(file_path)})
    assert result.success
    assert file_path.is_file()
    # 3. write_file
    content = "Hello, Jarvis!"
    result = await engine.run("write_file", {"path": str(file_path), "content": content})
    assert result.success
    assert file_path.read_text(encoding="utf-8") == content
    # 4. copy_file
    copy_path = base / "copy.txt"
    result = await engine.run("copy", {"source": str(file_path), "destination": str(copy_path)})
    assert result.success
    assert copy_path.is_file()
    assert copy_path.read_text(encoding="utf-8") == content
    # 5. move_file (rename copy to moved.txt)
    moved_path = base / "moved.txt"
    result = await engine.run("move", {"source": str(copy_path), "destination": str(moved_path)})
    assert result.success
    assert not copy_path.exists()
    assert moved_path.is_file()
    # 6. rename_file (rename moved.txt to final.txt)
    final_path = base / "final.txt"
    result = await engine.run("rename", {"source": str(moved_path), "destination": str(final_path)})
    assert result.success
    assert not moved_path.exists()
    assert final_path.is_file()
    # Verify final content unchanged
    assert final_path.read_text(encoding="utf-8") == content

@pytest.mark.asyncio
async def test_dry_run_create_folder(tmp_path: Path):
    engine = get_mutation_engine()
    dry_path = tmp_path / "dry_folder"
    result = await engine.run("create_folder", {"path": str(dry_path), "dry_run": True})
    assert result.success is True
    assert dry_path.exists() is False
    assert result.data["dry_run"] is True
