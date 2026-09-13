import json
import types

import pytest

from app.workers.document_worker.agent.worker_agent import DocumentWorkerAgent


def make_agent(monkeypatch, responses, objective="Fix the report", allowed=None, scope="/tmp"):
    allowed = allowed or ["inspect_docx", "normalize_headings", "backup_docx"]
    agent = DocumentWorkerAgent(objective, allowed, scope)

    # Force availability and script the LLM replies
    monkeypatch.setattr(agent, "available", True)
    agent._llm = types.SimpleNamespace()
    agent._llm._chat = _scripted_chat(responses)
    return agent


def _scripted_chat(responses):
    async def fake_chat(messages):
        return responses.pop(0)

    return fake_chat


# ── availability ────────────────────────────────────────────────────────


def test_agent_unavailable_without_key(monkeypatch):
    monkeypatch.setattr(
        "app.workers.document_worker.agent.worker_agent.get_worker_api_key", lambda: None
    )
    agent = DocumentWorkerAgent("do x", ["inspect_docx"], "/tmp")
    assert agent.available is False


# ── decision parsing ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_decide_tool_injects_fs_scope(monkeypatch):
    agent = make_agent(
        monkeypatch,
        [json.dumps({"action": "tool", "tool": "inspect_docx", "params": {}})],
    )
    decision = await agent.decide_next_step()
    assert decision["action"] == "tool"
    assert decision["tool"] == "inspect_docx"
    assert decision["params"]["fs_scope"] == "/tmp"


@pytest.mark.asyncio
async def test_decide_done(monkeypatch):
    agent = make_agent(
        monkeypatch,
        [json.dumps({"action": "done", "summary": "All headings fixed."})],
    )
    decision = await agent.decide_next_step()
    assert decision == {"action": "done", "summary": "All headings fixed."}


@pytest.mark.asyncio
async def test_decide_rejects_disallowed_tool(monkeypatch):
    agent = make_agent(
        monkeypatch,
        [json.dumps({"action": "tool", "tool": "delete_file", "params": {}})],
    )
    decision = await agent.decide_next_step()
    assert decision["action"] == "fail"
    assert "delete_file" in decision["reason"]


@pytest.mark.asyncio
async def test_decide_tolerates_prose_around_json(monkeypatch):
    agent = make_agent(
        monkeypatch,
        ['Here is my decision:\n{"action": "done", "summary": "ok"} hope that helps'],
    )
    decision = await agent.decide_next_step()
    assert decision["action"] == "done"


@pytest.mark.asyncio
async def test_decide_unparseable_fails_gracefully(monkeypatch):
    agent = make_agent(monkeypatch, ["definitely not json"])
    decision = await agent.decide_next_step()
    assert decision["action"] == "fail"
    assert "parse" in decision["reason"].lower()


@pytest.mark.asyncio
async def test_decide_llm_error_fails_gracefully(monkeypatch):
    agent = make_agent(monkeypatch, [])

    async def boom(messages):
        raise RuntimeError("network down")

    agent._llm._chat = boom
    decision = await agent.decide_next_step()
    assert decision["action"] == "fail"
    assert "network down" in decision["reason"]


# ── scope scan: files listed in the system prompt ───────────────────────


def test_scope_files_appear_in_system_prompt(monkeypatch, tmp_path):
    (tmp_path / "report.docx").write_bytes(b"fake")
    (tmp_path / "notes.docx").write_bytes(b"fake")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "deep.docx").write_bytes(b"fake")

    agent = DocumentWorkerAgent("do x", ["inspect_docx"], str(tmp_path))
    # no API key in tests → unavailable, so exercise the scan + prompt directly
    files = agent._scan_scope(str(tmp_path))
    assert str(tmp_path / "report.docx") in files
    assert str(tmp_path / "notes.docx") in files
    assert str(sub / "deep.docx") in files

    from app.workers.document_worker.agent.prompts import worker_system_prompt

    prompt = worker_system_prompt(["inspect_docx"], "do x", files)
    assert "report.docx" in prompt
    assert "FILES ALREADY IN YOUR SCOPE" in prompt


def test_scope_scan_tolerates_bad_path():
    agent = DocumentWorkerAgent.__new__(DocumentWorkerAgent)
    assert agent._scan_scope("Z:/nonexistent/path/xyz") == []


# ── step recording feeds the next decision ──────────────────────────────


@pytest.mark.asyncio
async def test_record_step_visible_in_next_prompt(monkeypatch):
    captured = []

    async def fake_chat(messages):
        captured.append(messages[-1]["content"])
        return json.dumps({"action": "done", "summary": "done"})

    agent = make_agent(monkeypatch, [])
    agent._llm._chat = fake_chat

    agent.record_step("inspect_docx", True, output={"paragraph_count": 5, "nested": {"x": 1}})
    agent.record_step("normalize_headings", False, error="file locked")
    agent.inject_intervention("Skip the backup, go faster")

    decision = await agent.decide_next_step()
    assert decision["action"] == "done"
    user_msg = captured[0]
    assert "1. inspect_docx → ok" in user_msg
    assert "2. normalize_headings → FAILED: file locked" in user_msg
    assert "Skip the backup" in user_msg
    # non‑scalar output fields dropped (keeps the prompt tiny)
    assert "nested" not in user_msg
