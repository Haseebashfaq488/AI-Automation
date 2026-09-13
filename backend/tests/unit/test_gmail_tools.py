import pytest
from app.core.exceptions import ValidationError
from app.core.execution_engine import ExecutionEngine
from app.registry import registry
from app.modules.gmail.tools import send_email_tool
from app.modules.gmail.tools.send_email_tool import SendEmailTool


@pytest.fixture(autouse=True)
def setup_registry(monkeypatch):
    # ensure the tool is registered
    registry.register(SendEmailTool())
    # force the "no credentials" path regardless of any real token.json
    monkeypatch.setattr(send_email_tool, "_load_token_path", lambda: None)
    yield


@pytest.mark.asyncio
async def test_send_email_happy_path_no_creds():
    # Without token.json the tool raises RuntimeError -> engine returns success=False
    engine = ExecutionEngine(registry)
    result = await engine.run("send_email", {
        "to": "test@example.com",
        "subject": "Hello",
        "body": "World",
    })
    assert result.success == False
    assert "credentials not found" in result.error["message"]


@pytest.mark.asyncio
async def test_send_email_missing_params():
    engine = ExecutionEngine(registry)
    with pytest.raises(ValidationError) as exc_info:
        await engine.run("send_email", {"to": "a@b.com"})
    assert "Missing required parameters" in str(exc_info.value)


@pytest.mark.asyncio
async def test_send_email_with_missing_creds_error():
    engine = ExecutionEngine(registry)
    result = await engine.run("send_email", {
        "to": "test@example.com",
        "subject": "Hello",
        "body": "World",
    })
    assert result.success == False
    assert result.error is not None
    assert "credentials not found" in result.error["message"]


@pytest.mark.asyncio
async def test_send_email_missing_attachment_fails_fast():
    # attachments are validated before credentials / Gmail API access
    engine = ExecutionEngine(registry)
    result = await engine.run("send_email", {
        "to": "test@example.com",
        "body": "World",
        "attachments": ["C:\\definitely\\not\\here.txt"],
    })
    assert result.success == False
    assert "Attachment not found" in result.error["message"]


@pytest.mark.asyncio
async def test_send_email_mock_mode_with_attachment(monkeypatch, tmp_path):
    monkeypatch.setenv("GMAIL_MOCK", "1")
    f = tmp_path / "report.txt"
    f.write_text("hello attachment")
    engine = ExecutionEngine(registry)
    result = await engine.run("send_email", {
        "to": "test@example.com",
        "subject": "Hello",
        "body": "World",
        "attachments": [str(f)],
    })
    assert result.success == True
    assert result.data["sent"] == True
    assert result.data["attachments"] == ["report.txt"]
    assert result.data["mock"] == True