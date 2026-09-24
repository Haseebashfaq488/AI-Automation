"""Tests for the WhatsApp module using a fake sidecar client."""
import base64
import time

import pytest

from app.core.execution_engine import ExecutionEngine
from app.registry import registry
from app.modules.whatsapp.helpers import client as wa_client_module
from app.modules.whatsapp.helpers.validation import (
    normalize_phone, to_chat_id, validate_chat_action, resolve_recipient,
)
from app.modules.whatsapp.skills.send_report import SendReportSkill
from app.modules.whatsapp.skills.unread_digest import UnreadDigestSkill
from app.modules.whatsapp.pipelines.downloads_notifier_pipeline import DownloadsNotifierPipeline
from app.modules.whatsapp.pipelines.photo_backup_pipeline import PhotoBackupPipeline
from app.modules.whatsapp.pipelines.daily_digest_pipeline import DailyDigestPipeline


class FakeWhatsAppClient:
    """Records calls and returns canned sidecar responses."""

    def __init__(self):
        self.calls = []
        self.chats = [
            {"id": "111@c.us", "name": "Mom", "unread": 2, "isGroup": False, "pinned": False, "timestamp": 1},
            {"id": "222@g.us", "name": "Family Group", "unread": 0, "isGroup": True, "pinned": True, "timestamp": 2},
        ]
        self.messages = [
            {"id": "m1", "body": "call me when free", "from": "111@c.us", "to": "me@c.us",
             "fromMe": False, "timestamp": 100, "type": "chat", "hasMedia": False, "caption": None, "author": None},
            {"id": "m2", "body": "sure, tonight", "from": "me@c.us", "to": "111@c.us",
             "fromMe": True, "timestamp": 101, "type": "chat", "hasMedia": False, "caption": None, "author": None},
            {"id": "m3", "body": "don't forget the apples", "from": "111@c.us", "to": "me@c.us",
             "fromMe": False, "timestamp": 102, "type": "chat", "hasMedia": False, "caption": None, "author": None},
        ]

    async def status(self):
        return {"state": "ready", "qr": None, "pushname": "Tester"}

    async def list_chats(self, limit=50):
        self.calls.append(("list_chats", limit))
        return list(self.chats)

    async def get_messages(self, chat, limit=20):
        self.calls.append(("get_messages", chat, limit))
        return {"chat": {"id": chat, "name": "Mom"}, "messages": list(self.messages[:limit])}

    async def send_message(self, to, message):
        self.calls.append(("send_message", to, message))
        return {"sent": True, "to": to if "@" in to else "111@c.us", "messageId": "sent1"}

    async def send_file(self, to, path, caption=None):
        self.calls.append(("send_file", to, path, caption))
        return {"sent": True, "to": to, "messageId": "sent2", "filename": str(path).split("\\")[-1]}

    async def chat_action(self, chat, action):
        self.calls.append(("chat_action", chat, action))
        return {"ok": True, "chat": chat, "action": action}

    async def group_action(self, action, chat=None, name=None, participants=None):
        self.calls.append(("group_action", action, chat, name, participants))
        return {"ok": True, "action": action}

    async def contacts(self, query=None):
        return [{"id": "111@c.us", "name": "Mom", "number": "111", "pushname": "Mom", "isGroup": False}]

    async def chat_info(self, chat):
        return {"id": chat, "name": "Mom", "isGroup": False, "unread": 2}

    async def download_media(self, chat, limit=50):
        png = base64.b64encode(b"\x89PNG fake").decode()
        return {"chat": {"id": chat, "name": "Mom"}, "media": [
            {"messageId": "m9", "filename": "photo.png", "mimetype": "image/png",
             "caption": None, "timestamp": time.time(), "data": png},
        ]}


@pytest.fixture
def engine():
    return ExecutionEngine(registry)


@pytest.fixture
def fake_client(monkeypatch):
    fake = FakeWhatsAppClient()
    monkeypatch.setattr(wa_client_module, "_client", fake)  # get_client() returns this
    return fake


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def test_normalize_phone():
    assert normalize_phone("+1 (555) 123-4567") == "15551234567"
    assert normalize_phone("001-55-11") == "0015511"


def test_to_chat_id():
    assert to_chat_id("+49 170 1234") == "491701234@c.us"
    with pytest.raises(ValueError):
        to_chat_id("abc")


def test_validate_chat_action():
    assert validate_chat_action("PIN") == "pin"
    with pytest.raises(ValueError):
        validate_chat_action("explode")


def test_resolve_recipient():
    assert resolve_recipient("+1 555 000 1111") == "15550001111@c.us"
    assert resolve_recipient("Mom") == "Mom"
    with pytest.raises(ValueError):
        resolve_recipient("   ")


# ---------------------------------------------------------------------------
# Tools via the execution engine
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_message_tool(engine, fake_client):
    result = await engine.run("send_message", {"to": "Mom", "message": "hi mom"})
    assert result.success
    assert ("send_message", "Mom", "hi mom") in fake_client.calls
    assert result.data["sent"] is True


@pytest.mark.asyncio
async def test_send_message_resolves_phone_number(engine, fake_client):
    result = await engine.run("send_message", {"to": "+1 555 000 1111", "message": "hi"})
    assert result.success
    assert fake_client.calls[0][1] == "15550001111@c.us"


@pytest.mark.asyncio
async def test_send_message_dry_run(engine, fake_client):
    result = await engine.run("send_message", {"to": "Mom", "message": "hi", "dry_run": True})
    assert result.success and result.data["dry_run"] is True
    assert not fake_client.calls


@pytest.mark.asyncio
async def test_send_file_tool_validates_path(engine, fake_client, tmp_path):
    ok = tmp_path / "doc.txt"
    ok.write_text("x")
    result = await engine.run("send_file", {"to": "Mom", "path": str(ok)})
    assert result.success
    assert fake_client.calls[0][0] == "send_file"

    missing = await engine.run("send_file", {"to": "Mom", "path": str(tmp_path / "nope.txt")})
    assert not missing.success


@pytest.mark.asyncio
async def test_list_chats_tool(engine, fake_client):
    result = await engine.run("list_chats", {})
    assert result.success
    assert result.data["count"] == 2


@pytest.mark.asyncio
async def test_list_chats_unread_only(engine, fake_client):
    result = await engine.run("list_chats", {"unread_only": True})
    assert result.success
    assert result.data["count"] == 1
    assert result.data["chats"][0]["name"] == "Mom"


@pytest.mark.asyncio
async def test_get_messages_tool(engine, fake_client):
    result = await engine.run("get_messages", {"chat": "Mom", "limit": 2})
    assert result.success
    assert result.data["count"] == 2


@pytest.mark.asyncio
async def test_search_messages_tool(engine, fake_client):
    result = await engine.run("search_messages", {"chat": "Mom", "query": "apples"})
    assert result.success
    assert result.data["match_count"] == 1
    assert result.data["matches"][0]["id"] == "m3"


@pytest.mark.asyncio
async def test_manage_chat_tool(engine, fake_client):
    result = await engine.run("manage_chat", {"chat": "Family Group", "action": "mute"})
    assert result.success
    assert ("chat_action", "Family Group", "mute") in fake_client.calls

    bad = await engine.run("manage_chat", {"chat": "X", "action": "explode"})
    assert not bad.success


@pytest.mark.asyncio
async def test_manage_group_tool(engine, fake_client):
    result = await engine.run("manage_group", {
        "action": "create", "name": "Test Group", "participants": ["+49 170 1"]})
    assert result.success
    call = next(c for c in fake_client.calls if c[0] == "group_action")
    assert call[3] == "Test Group"
    assert call[4] == ["491701@c.us"]


@pytest.mark.asyncio
async def test_whatsapp_status_tool(engine, fake_client):
    result = await engine.run("whatsapp_status", {})
    assert result.success
    assert result.data["connected"] is True
    assert result.data["state"] == "ready"


@pytest.mark.asyncio
async def test_download_media_tool(engine, fake_client, tmp_path):
    dest = tmp_path / "media"
    result = await engine.run("download_media", {"chat": "Mom", "destination": str(dest)})
    assert result.success
    assert result.data["downloaded"] == 1
    assert (dest / "photo.png").exists()


# ---------------------------------------------------------------------------
# Sidecar-down behavior: clean failure, not a crash
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tool_reports_clean_error_when_sidecar_down(engine, monkeypatch):
    monkeypatch.setattr(wa_client_module, "_client", None)
    real = wa_client_module.WhatsAppClient(base_url="http://127.0.0.1:59999", timeout=2.0)
    monkeypatch.setattr(wa_client_module, "_client", real)
    try:
        result = await engine.run("list_chats", {})
        assert not result.success
        assert "not running" in result.error["message"]
    finally:
        await real.close()


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_report_skill_file(fake_client, tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text("hello report")
    result = await SendReportSkill().execute({"to": "Mom", "path": str(f)})
    assert result["sent"] is True
    call = next(c for c in fake_client.calls if c[0] == "send_message")
    assert "notes.txt" in call[2]
    assert "hello report" in call[2]


@pytest.mark.asyncio
async def test_send_report_skill_folder(fake_client, tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    result = await SendReportSkill().execute({"to": "Mom", "path": str(tmp_path)})
    assert result["sent"] is True
    call = next(c for c in fake_client.calls if c[0] == "send_message")
    assert "2 files" in call[2]


@pytest.mark.asyncio
async def test_unread_digest_skill(fake_client):
    result = await UnreadDigestSkill().execute({})
    assert result["unread_chats"] == 1
    assert "Mom" in result["digest"]
    assert "sent" not in result  # no 'to' -> not sent

    result2 = await UnreadDigestSkill().execute({"to": "Mom"})
    assert result2["sent"] is True


@pytest.mark.asyncio
async def test_get_unread_messages_tool(fake_client):
    from app.modules.whatsapp.tools.get_unread_messages import GetUnreadMessagesTool
    tool = GetUnreadMessagesTool()
    res = await tool.execute({"chat_limit": 10})
    assert res["unread_chat_count"] == 1
    assert res["total_unread_messages"] == 2
    assert len(res["chats"]) == 1
    assert res["chats"][0]["name"] == "Mom"
    assert "call me when free" in res["summary"]


@pytest.mark.asyncio
async def test_get_recent_whatsapp_activity_tool(fake_client):
    from app.modules.whatsapp.tools.get_recent_whatsapp_activity import GetRecentWhatsAppActivityTool
    tool = GetRecentWhatsAppActivityTool()
    res = await tool.execute({"chat_limit": 5, "messages_per_chat": 3})
    assert res["chat_count"] == 2
    assert len(res["chats"]) == 2
    assert "Mom" in res["summary"]
    assert "Family Group" in res["summary"]


# ---------------------------------------------------------------------------
# Pipelines
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_daily_digest_pipeline(fake_client):
    result = await DailyDigestPipeline().run({"to": "Me"})
    assert result["success"] is True
    assert result["sent"] is True
    assert "digest" in result


@pytest.mark.asyncio
async def test_downloads_notifier_pipeline(fake_client, tmp_path):
    # no fresh files -> no notification
    r0 = await DownloadsNotifierPipeline().run({
        "watch_dir": str(tmp_path), "to": "Me", "since_minutes": 60})
    assert r0["notified"] is False

    # fresh file -> notification sent
    time.sleep(0.05)
    (tmp_path / "movie.mkv").write_bytes(b"x" * 2048)
    r1 = await DownloadsNotifierPipeline().run({
        "watch_dir": str(tmp_path), "to": "Me", "since_minutes": 60})
    assert r1["notified"] is True
    assert "movie.mkv" in r1["message"]
    assert any(c[0] == "send_message" for c in fake_client.calls)


@pytest.mark.asyncio
async def test_photo_backup_pipeline(fake_client, tmp_path):
    result = await PhotoBackupPipeline().run({
        "chat": "Mom", "target_dir": str(tmp_path / "photos")})
    assert result["success"] is True
    assert result["count"] == 1
    saved = result["saved"][0]
    assert saved["path"].endswith("photo.png")
    from pathlib import Path
    assert Path(saved["path"]).exists()
