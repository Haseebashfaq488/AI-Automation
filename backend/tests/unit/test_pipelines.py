import os
import time

import pytest

from app.modules.file_management.pipelines.organize_photos_pipeline import OrganizePhotosPipeline
from app.modules.file_management.pipelines.dedupe_folder_pipeline import DedupeFolderPipeline
from app.modules.file_management.pipelines.backup_documents_pipeline import BackupDocumentsPipeline
from app.modules.file_management.pipelines.archive_old_files_pipeline import ArchiveOldFilesPipeline
from app.modules.file_management.pipelines.sort_by_date_pipeline import SortByDatePipeline


@pytest.mark.asyncio
async def test_organize_photos_pipeline(tmp_path):
    photos = tmp_path / "photos"
    photos.mkdir()
    img = photos / "pic.jpg"
    img.write_bytes(b"fake")
    # set mtime to October 2023
    ts = time.mktime((2023, 10, 15, 12, 0, 0, 0, 0, -1))
    os.utime(img, (ts, ts))
    (photos / "note.txt").write_text("not a photo")

    result = await OrganizePhotosPipeline().run({"source_dir": str(photos)})
    assert result["success"] is True
    assert result["count"] == 1
    assert (photos / "2023" / "10" / "pic.jpg").exists()
    assert (photos / "note.txt").exists()  # non-image untouched


@pytest.mark.asyncio
async def test_organize_photos_dry_run(tmp_path):
    photos = tmp_path / "photos"
    photos.mkdir()
    (photos / "a.png").write_bytes(b"x")
    result = await OrganizePhotosPipeline().run({"source_dir": str(photos), "dry_run": True})
    assert result["dry_run"] is True
    assert (photos / "a.png").exists()


@pytest.mark.asyncio
async def test_dedupe_folder_pipeline(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()
    (folder / "a.txt").write_text("same")
    (folder / "b.txt").write_text("same")
    (folder / "c.txt").write_text("unique")
    # make content identical but different size would not dup; add true dup with different name
    (folder / "d.bin").write_bytes(b"\x00\x01\x02")
    (folder / "e.bin").write_bytes(b"\x00\x01\x02")

    result = await DedupeFolderPipeline().run({"source_dir": str(folder)})
    assert result["success"] is True
    assert result["duplicate_count"] == 2
    review = folder / "duplicates"
    assert review.is_dir()
    remaining = {p.name for p in folder.iterdir() if p.is_file()}
    # one of each dup pair kept, extras moved
    assert len(remaining) == 3
    assert len(list(review.iterdir())) == 2


@pytest.mark.asyncio
async def test_backup_documents_pipeline_incremental(tmp_path):
    src = tmp_path / "docs"
    src.mkdir()
    (src / "a.txt").write_text("v1")
    sub = src / "sub"
    sub.mkdir()
    (sub / "b.txt").write_text("v1")
    backup = tmp_path / "backup"

    r1 = await BackupDocumentsPipeline().run({"source_dir": str(src), "backup_dir": str(backup)})
    assert r1["copied_count"] == 2
    assert (backup / "a.txt").exists()
    assert (backup / "sub" / "b.txt").exists()

    # second run: nothing changed -> nothing copied
    r2 = await BackupDocumentsPipeline().run({"source_dir": str(src), "backup_dir": str(backup)})
    assert r2["copied_count"] == 0
    assert r2["skipped_count"] == 2

    # modify one file -> only that one is copied again
    time.sleep(0.05)
    (src / "a.txt").write_text("v2")
    r3 = await BackupDocumentsPipeline().run({"source_dir": str(src), "backup_dir": str(backup)})
    assert r3["copied_count"] == 1
    assert r3["copied"][0].endswith("a.txt")
    assert (backup / "a.txt").read_text() == "v2"


@pytest.mark.asyncio
async def test_archive_old_files_pipeline(tmp_path):
    folder = tmp_path / "old"
    folder.mkdir()
    old_file = folder / "report_2020.txt"
    old_file.write_text("old data")
    # mtime ~ 2 years ago
    ts = time.time() - 2 * 365 * 24 * 3600
    os.utime(old_file, (ts, ts))
    recent = folder / "current.txt"
    recent.write_text("new")

    result = await ArchiveOldFilesPipeline().run({"source_dir": str(folder), "older_than_months": 12})
    assert result["success"] is True
    assert result["archived_count"] == 1
    assert not old_file.exists()
    assert recent.exists()
    import zipfile
    with zipfile.ZipFile(result["zip_path"]) as zf:
        assert zf.namelist() == ["report_2020.txt"]


@pytest.mark.asyncio
async def test_archive_old_files_nothing_old(tmp_path):
    folder = tmp_path / "fresh"
    folder.mkdir()
    (folder / "new.txt").write_text("x")
    result = await ArchiveOldFilesPipeline().run({"source_dir": str(folder), "older_than_months": 12})
    assert result["archived"] == []
    assert result["zip_path"] is None


@pytest.mark.asyncio
async def test_sort_by_date_pipeline(tmp_path):
    folder = tmp_path / "misc"
    folder.mkdir()
    f1 = folder / "jan.txt"
    f1.write_text("1")
    ts1 = time.mktime((2024, 1, 10, 12, 0, 0, 0, 0, -1))
    os.utime(f1, (ts1, ts1))
    f2 = folder / "mar.txt"
    f2.write_text("2")
    ts2 = time.mktime((2024, 3, 10, 12, 0, 0, 0, 0, -1))
    os.utime(f2, (ts2, ts2))

    result = await SortByDatePipeline().run({"source_dir": str(folder)})
    assert result["success"] is True
    assert result["count"] == 2
    assert (folder / "2024-01" / "jan.txt").exists()
    assert (folder / "2024-03" / "mar.txt").exists()
