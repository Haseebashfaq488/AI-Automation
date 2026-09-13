import pytest

from app.core.execution_engine import ExecutionEngine
from app.registry import registry


@pytest.fixture
def engine():
    return ExecutionEngine(registry)


@pytest.mark.asyncio
async def test_search_content_finds_matches(engine, tmp_path):
    (tmp_path / "a.txt").write_text("hello world\nfoo bar\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("HELLO again\n", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.txt").write_text("nothing here\n", encoding="utf-8")

    result = await engine.run("search_content", {"path": str(tmp_path), "query": "hello"})
    assert result.success
    assert result.data["match_count"] == 2  # case-insensitive by default, recursive
    files = {m["file"] for m in result.data["matches"]}
    assert str(tmp_path / "a.txt") in files
    assert str(tmp_path / "b.txt") in files
    # line number is reported
    a_match = next(m for m in result.data["matches"] if m["file"].endswith("a.txt"))
    assert a_match["line"] == 1


@pytest.mark.asyncio
async def test_search_content_case_sensitive_and_non_recursive(engine, tmp_path):
    (tmp_path / "a.txt").write_text("Hello\n", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.txt").write_text("hello\n", encoding="utf-8")

    r1 = await engine.run("search_content", {
        "path": str(tmp_path), "query": "hello", "case_sensitive": True, "recursive": False,
    })
    assert r1.success
    assert r1.data["match_count"] == 0

    r2 = await engine.run("search_content", {
        "path": str(tmp_path), "query": "Hello", "case_sensitive": True, "recursive": False,
    })
    assert r2.data["match_count"] == 1

    r3 = await engine.run("search_content", {"path": str(tmp_path), "query": "hello", "recursive": True})
    assert r3.data["match_count"] == 2


@pytest.mark.asyncio
async def test_search_content_single_file_and_max_results(engine, tmp_path):
    f = tmp_path / "log.txt"
    f.write_text("error\nok\nerror\nerror\n", encoding="utf-8")
    result = await engine.run("search_content", {"path": str(f), "query": "error", "max_results": 2})
    assert result.success
    assert result.data["match_count"] == 2
    assert result.data["truncated"] is True
