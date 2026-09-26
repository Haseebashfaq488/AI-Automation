"""Unit tests for MemoryVectorIndex on-demand semantic retrieval."""
import pytest
from pathlib import Path

from app.modules.antigravity.memory_vector_index import MemoryVectorIndex


@pytest.fixture
def sample_memory_file(tmp_path: Path) -> Path:
    mem_file = tmp_path / "JARVIS_MEMORY.md"
    mem_file.write_text(
        "# 🧠 JARVIS LIVING MEMORY\n\n"
        "## 👤 User Profile & Invariants\n"
        "- Owner / User: Dum Dum\n"
        "- Phone Number: +923098956995\n\n"
        "## 💡 Active Preferences & Habits\n"
        "- GUI Preference: Dum Dum prefers GUI/UI-based applications over command-line/terminal interfaces.\n"
        "- Communication Channel: Dum Dum's primary email address is haseebhamza789@gmail.com.\n"
        "- Delivery Preference: Dum Dum explicitly prefers receiving project summary artifacts via email.\n\n"
        "## 📁 Active Projects & Workspaces\n"
        "- Application Project: D:/calculator (interactive GUI-based graphical calculator).\n"
        "- Primary Sandbox: D:/workspace (clean dedicated directory for autonomous workers).\n\n"
        "## 📝 Recent Scratchpad (Rolling Active Notes)\n"
        "- [2026-09-24 21:09] User expects project summary reports to include step-by-step launch instructions.\n",
        encoding="utf-8",
    )
    return mem_file


def test_memory_vector_index_extracts_documents(sample_memory_file: Path):
    index = MemoryVectorIndex(memory_path=sample_memory_file)
    assert len(index._documents) >= 5
    # Profile & invariants should NOT be indexed as separate documents
    assert not any("Owner / User: Dum Dum" in d for d in index._documents)
    # Preferences and projects should be indexed
    assert any("GUI/UI-based" in d for d in index._documents)
    assert any("D:/calculator" in d for d in index._documents)


def test_memory_vector_index_bypasses_greetings(sample_memory_file: Path):
    index = MemoryVectorIndex(memory_path=sample_memory_file)
    # Short greetings must return [] to avoid token bloat
    assert index.query_relevant_facts("hi bubbles") == []
    assert index.query_relevant_facts("hello") == []
    assert index.query_relevant_facts("good morning") == []
    assert index.query_relevant_facts("how are you doing today?") == []


def test_memory_vector_index_retrieves_relevant_facts(sample_memory_file: Path):
    index = MemoryVectorIndex(memory_path=sample_memory_file)

    # Email query
    email_facts = index.query_relevant_facts("can you send the report to my email?")
    assert len(email_facts) > 0
    assert any("email" in f.lower() or "haseebhamza789" in f.lower() for f in email_facts)

    # Calculator project query
    calc_facts = index.query_relevant_facts("let's continue working on the calculator app")
    assert len(calc_facts) > 0
    assert any("calculator" in f.lower() for f in calc_facts)


def test_memory_vector_index_refreshes_after_update(sample_memory_file: Path):
    index = MemoryVectorIndex(memory_path=sample_memory_file)
    initial_count = len(index._documents)

    # Append a new preference to the file
    content = sample_memory_file.read_text(encoding="utf-8")
    content += "\n- Framework: Dum Dum loves building web frontends with Next.js 16.\n"
    sample_memory_file.write_text(content, encoding="utf-8")

    index.refresh()
    assert len(index._documents) == initial_count + 1

    results = index.query_relevant_facts("what frontend framework should we use?")
    assert any("Next.js" in r for r in results)
