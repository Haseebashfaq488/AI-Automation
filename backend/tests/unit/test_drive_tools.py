import pytest
from app.core.exceptions import ValidationError
from app.core.execution_engine import ExecutionEngine
from app.registry import registry
from app.modules.drive.tools.list_drive_files import ListDriveFilesTool
from app.modules.drive.tools.read_drive_file import ReadDriveFileTool
from app.modules.drive.tools.upload_drive_file import UploadDriveFileTool
from app.modules.drive.skills.search_drive import SearchDriveSkill
from app.modules.drive.helpers import drive_client


@pytest.fixture(autouse=True)
def setup_drive_registry(monkeypatch):
    registry.register(ListDriveFilesTool())
    registry.register(ReadDriveFileTool())
    registry.register(UploadDriveFileTool())
    registry.register(SearchDriveSkill())
    # Ensure no-creds fallback unless explicitly set to mock
    monkeypatch.setattr(drive_client, "get_drive_creds", lambda: None)
    yield


@pytest.mark.asyncio
async def test_list_drive_files_mock_mode(monkeypatch):
    monkeypatch.setenv("DRIVE_MOCK", "1")
    engine = ExecutionEngine(registry)
    result = await engine.run("list_drive_files", {"page_size": 5})

    assert result.success is True
    assert result.data["success"] is True
    assert len(result.data["files"]) == 3
    assert result.data["files"][0]["name"] == "Project Roadmap 2026.docx"


@pytest.mark.asyncio
async def test_list_drive_files_no_creds(monkeypatch):
    monkeypatch.delenv("DRIVE_MOCK", raising=False)
    engine = ExecutionEngine(registry)
    result = await engine.run("list_drive_files", {})

    assert result.success is True
    assert result.data["success"] is False
    assert "credentials not found" in result.data["error"].lower()


@pytest.mark.asyncio
async def test_read_drive_file_mock_mode(monkeypatch):
    monkeypatch.setenv("DRIVE_MOCK", "1")
    engine = ExecutionEngine(registry)
    result = await engine.run("read_drive_file", {"file_id": "mock_file_123"})

    assert result.success is True
    assert result.data["success"] is True
    assert "Roadmap" in result.data["content"]


@pytest.mark.asyncio
async def test_read_drive_file_missing_id():
    engine = ExecutionEngine(registry)
    with pytest.raises(ValidationError):
        await engine.run("read_drive_file", {})


@pytest.mark.asyncio
async def test_upload_drive_file_mock_mode(monkeypatch, tmp_path):
    monkeypatch.setenv("DRIVE_MOCK", "1")
    test_file = tmp_path / "test_doc.txt"
    test_file.write_text("sample drive content")

    engine = ExecutionEngine(registry)
    result = await engine.run("upload_drive_file", {
        "path": str(test_file),
        "name": "Custom Drive Name.txt",
    })

    assert result.success is True
    assert result.data["success"] is True
    assert result.data["name"] == "Custom Drive Name.txt"
    assert result.data["file_id"] == "mock_uploaded_drive_file_id"


@pytest.mark.asyncio
async def test_upload_drive_file_missing_local_file(monkeypatch):
    monkeypatch.setenv("DRIVE_MOCK", "1")
    engine = ExecutionEngine(registry)
    result = await engine.run("upload_drive_file", {
        "path": "C:\\nonexistent\\path\\file.txt",
    })

    assert result.success is True
    assert result.data["success"] is False
    assert "not found" in result.data["error"].lower()


@pytest.mark.asyncio
async def test_search_drive_mock_mode(monkeypatch):
    monkeypatch.setenv("DRIVE_MOCK", "1")
    engine = ExecutionEngine(registry)
    result = await engine.run("search_drive", {"query": "Roadmap", "file_type": "document"})

    assert result.success is True
    assert result.data["success"] is True
    assert len(result.data["files"]) == 2
    assert "Roadmap" in result.data["files"][0]["name"]
