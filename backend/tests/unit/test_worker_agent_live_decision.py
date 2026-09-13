import pytest
from app.workers.document_worker.agent.config import get_worker_api_key
from app.workers.document_worker.agent.worker_agent import DocumentWorkerAgent


@pytest.mark.skipif(
    not get_worker_api_key(),
    reason="Worker LLM API key not configured in environment",
)
@pytest.mark.asyncio
async def test_worker_agent_live_llm_tool_decision():
    """Verify that the real LLM API analyzes the assigned task and autonomously

    decides the appropriate tool to invoke (e.g. create_docx).
    """
    objective = "Create a new document quarterly_report.docx with title 'Q3 Financial Report'"
    allowed_tools = [
        "create_docx",
        "add_heading",
        "add_paragraph",
        "add_table",
        "inspect_docx",
    ]
    fs_scope = "D:/Ai automation backend/backend/demo_workspace"

    agent = DocumentWorkerAgent(
        objective=objective,
        allowed_tools=allowed_tools,
        fs_scope=fs_scope,
    )

    assert agent.available is True, "Agent must be available when an API key is provided"

    # 1. Ask the live LLM API for the first step decision
    decision = await agent.decide_next_step()

    # Verify decision structure
    assert isinstance(decision, dict)
    assert decision.get("action") == "tool", f"Expected action 'tool', got {decision}"
    assert decision.get("tool") in allowed_tools, f"Tool {decision.get('tool')} not in allowed_tools"
    # For a create document objective, the LLM should sensibly select 'create_docx'
    assert decision.get("tool") == "create_docx"

    params = decision.get("params", {})
    assert "path" in params
    assert params["path"].endswith(".docx")
    assert params.get("fs_scope") == fs_scope


@pytest.mark.skipif(
    not get_worker_api_key(),
    reason="Worker LLM API key not configured in environment",
)
@pytest.mark.asyncio
async def test_worker_agent_live_llm_multi_step_completion():
    """Verify that after receiving tool execution feedback, the real LLM

    advances to the next tool or completes the goal ('done').
    """
    objective = "Inspect report.docx"
    allowed_tools = ["inspect_docx", "read_docx"]
    fs_scope = "D:/Ai automation backend/backend/demo_workspace"

    agent = DocumentWorkerAgent(
        objective=objective,
        allowed_tools=allowed_tools,
        fs_scope=fs_scope,
    )

    # First step: LLM should decide to inspect
    d1 = await agent.decide_next_step()
    assert d1.get("action") == "tool"
    assert d1.get("tool") == "inspect_docx"

    # Simulate tool execution success
    agent.record_step(
        "inspect_docx",
        success=True,
        output={"paragraph_count": 10, "headings": ["Intro", "Results"]},
    )

    # Second step: Given the objective was simply to inspect report.docx and it's done,
    # the LLM should recognize completion and return action 'done'.
    d2 = await agent.decide_next_step()
    assert d2.get("action") in ("done", "tool")
    if d2.get("action") == "done":
        assert "summary" in d2
