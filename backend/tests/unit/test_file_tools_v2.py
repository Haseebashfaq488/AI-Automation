import os
import time
import zipfile

import pytest

from app.core.execution_engine import ExecutionEngine
from app.registry import registry
from app.modules.file_management.helpers.trash import TRASH_DIR


@pytest.fixture
def engine():
    return ExecutionEngine(registry)


# ---------------------------------------------------------------------------
# delete_file / delete_folder
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_file_moves_to_trash(engine, tmp_path):
    f = tmp_path / "bye.txt"
    f.write_text("x")
    result = await engine.run("delete_file", {"path": str(f)})
    assert result.success
    assert not f.exists()
    trash_path = result.data["trash_path"]
    assert os.path.exists(trash_path)
    assert str(TRASH_DIR) in trash_path
    assert result.data["permanent"] is False


@pytest.mark.asyncio
async def test_delete_file_permanent(engine, tmp_path):
    f = tmp_path / "gone.txt"
    f.write_text("x")
    result = await engine.run("delete_file", {"path": str(f), "permanent": True})
    assert result.success
    assert not f.exists()
    assert result.data["permanent"] is True


@pytest.mark.asyncio
async def test_delete_folder_moves_to_trash(engine, tmp_path):
    d = tmp_path / "folder"
    d.mkdir()
    (d / "inner.txt").write_text("x")
    result = await engine.run("delete_folder", {"path": str(d)})
    assert result.success
    assert not d.exists()
    assert os.path.exists(result.data["trash_path"])


@pytest.mark.asyncio
async def test_delete_file_dry_run(engine, tmp_path):
    f = tmp_path / "keep.txt"
    f.write_text("x")
    result = await engine.run("delete_file", {"path": str(f), "dry_run": True})
    assert result.success and result.data["dry_run"] is True
    assert f.exists()


# ---------------------------------------------------------------------------
# archive / extract
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_archive_folder_and_extract_roundtrip(engine, tmp_path):
    src = tmp_path / "docs"
    src.mkdir()
    (src / "a.txt").write_text("aaa")
    (src / "b.txt").write_text("bbb")
    zip_path = tmp_path / "out" / "docs.zip"

    result = await engine.run("archive", {"source": str(src), "destination": str(zip_path)})
    assert result.success
    assert zip_path.exists()
    assert result.data["file_count"] == 2

    dest = tmp_path / "restored"
    result2 = await engine.run("extract", {"path": str(zip_path), "destination": str(dest)})
    assert result2.success
    assert (dest / "a.txt").read_text() == "aaa"
    assert (dest / "b.txt").read_text() == "bbb"


@pytest.mark.asyncio
async def test_extract_default_destination(engine, tmp_path):
    f = tmp_path / "one.txt"
    f.write_text("1")
    zip_path = tmp_path / "one.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(f, arcname="one.txt")
    result = await engine.run("extract", {"path": str(zip_path)})
    assert result.success
    assert (tmp_path / "one" / "one.txt").read_text() == "1"


@pytest.mark.asyncio
async def test_extract_rejects_zip_slip(engine, tmp_path):
    zip_path = tmp_path / "evil.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../../escaped.txt", "bad")
    result = await engine.run("extract", {"path": str(zip_path), "destination": str(tmp_path / "out")})
    assert not result.success
    assert "nsafe" in result.error["message"] or "Unsafe" in result.error["message"]


# ---------------------------------------------------------------------------
# touch
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_touch_creates_missing_file(engine, tmp_path):
    f = tmp_path / "new" / "touched.txt"
    result = await engine.run("touch", {"path": str(f)})
    assert result.success
    assert f.exists()
    assert result.data["created"] is True


@pytest.mark.asyncio
async def test_touch_updates_timestamp(engine, tmp_path):
    f = tmp_path / "t.txt"
    f.write_text("x")
    old = time.time() - 10000
    os.utime(f, (old, old))
    result = await engine.run("touch", {"path": str(f)})
    assert result.success
    assert result.data["created"] is False
    assert f.stat().st_mtime > old


# ---------------------------------------------------------------------------
# bulk_rename
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_bulk_rename_with_counter(engine, tmp_path):
    for name in ["z.txt", "a.txt", "m.txt"]:
        (tmp_path / name).write_text(name)
    result = await engine.run("bulk_rename", {"path": str(tmp_path), "pattern": "file_###"})
    assert result.success
    assert result.data["renamed"] == 3
    assert (tmp_path / "file_001.txt").exists()
    assert (tmp_path / "file_002.txt").exists()
    assert (tmp_path / "file_003.txt").exists()
    assert not (tmp_path / "a.txt").exists()


@pytest.mark.asyncio
async def test_bulk_rename_extension_filter_and_start_index(engine, tmp_path):
    (tmp_path / "p.jpg").write_text("1")
    (tmp_path / "q.jpg").write_text("2")
    (tmp_path / "r.png").write_text("3")
    result = await engine.run("bulk_rename", {
        "path": str(tmp_path), "pattern": "img_##", "extension": "jpg", "start_index": 5,
    })
    assert result.success
    assert result.data["renamed"] == 2
    assert (tmp_path / "img_05.jpg").exists()
    assert (tmp_path / "img_06.jpg").exists()
    assert (tmp_path / "r.png").exists()  # untouched


@pytest.mark.asyncio
async def test_bulk_rename_dry_run(engine, tmp_path):
    (tmp_path / "a.txt").write_text("1")
    result = await engine.run("bulk_rename", {"path": str(tmp_path), "pattern": "x_#", "dry_run": True})
    assert result.success and result.data["dry_run"] is True
    assert (tmp_path / "a.txt").exists()


# ---------------------------------------------------------------------------
# append_file
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_append_file_creates_and_appends(engine, tmp_path):
    f = tmp_path / "log.txt"
    r1 = await engine.run("append_file", {"path": str(f), "content": "line1\n"})
    assert r1.success and f.read_text() == "line1\n"
    r2 = await engine.run("append_file", {"path": str(f), "content": "line2\n"})
    assert r2.success
    assert f.read_text() == "line1\nline2\n"
    assert r2.data["size"] == len("line1\nline2\n")
