import asyncio
import pytest
from app.core.events.bus import get_event_bus
from app.core.events.orchestrator import TaskOrchestrator
from app.core.events.schema import EventType, JarvisEvent
from app.core.tool import BaseTool, RiskLevel
from app.registry import registry


class MockWhatsAppTool(BaseTool):
    name = "mock_send_file"
    description = "Mock send file tool"
    risk = RiskLevel.LOW
    category = "tool"
    input_schema = {
        "type": "object",
        "properties": {
            "to": {"type": "string"},
            "path": {"type": "string"},
            "caption": {"type": "string"},
        },
        "required": ["to", "path"],
    }

    def __init__(self):
        super().__init__()
        self.executed_calls = []

    async def execute(self, params: dict) -> dict:
        self.executed_calls.append(params)
        return {"status": "sent", "path": params.get("path"), "to": params.get("to")}


@pytest.mark.asyncio
async def test_task_orchestrator_chains_worker_completion():
    # Register mock tool
    mock_tool = MockWhatsAppTool()
    registry.register(mock_tool)

    orchestrator = TaskOrchestrator()
    orchestrator.start()

    session_id = "ws_test_session_123"
    hook = orchestrator.register_hook(
        target_session_id=session_id,
        action_tool="mock_send_file",
        action_params={"to": "+923098956995", "path": "{worker.artifact}", "caption": "Report ready"},
        description="Send report to WhatsApp",
    )

    assert hook.target_session_id == session_id
    assert not hook.executed

    bus = get_event_bus()
    captured_actions = []

    def on_autonomous_action(evt: JarvisEvent):
        captured_actions.append(evt)

    bus.on(EventType.AUTONOMOUS_ACTION_EXECUTED, on_autonomous_action)

    # Emit WORKER_COMPLETED
    completion_evt = JarvisEvent(
        event_type=EventType.WORKER_COMPLETED,
        source=f"worker:{session_id}",
        title="Worker Completed",
        summary="Done",
        data={
            "session_id": session_id,
            "success": True,
            "artifacts": ["D:/workspace/report.pdf"],
            "output": "Report successfully generated.",
        },
    )
    bus.publish(completion_evt)

    # Allow async task in orchestrator to run
    await asyncio.sleep(0.1)

    assert len(mock_tool.executed_calls) == 1
    call = mock_tool.executed_calls[0]
    assert call["to"] == "+923098956995"
    assert call["path"] == "D:/workspace/report.pdf"
    assert call["caption"] == "Report ready"

    assert len(captured_actions) == 1
    assert captured_actions[0].event_type == EventType.AUTONOMOUS_ACTION_EXECUTED


@pytest.mark.asyncio
async def test_task_orchestrator_auto_discovers_workspace_file(tmp_path, monkeypatch):
    # Create a test workspace file
    ws_file = tmp_path / "generated_doc.txt"
    ws_file.write_text("hello world")

    mock_tool = MockWhatsAppTool()
    mock_tool.name = "mock_send_file_2"
    registry.register(mock_tool)

    orchestrator = TaskOrchestrator()
    orchestrator.start()

    session_id = "ws_test_fallback_456"
    hook = orchestrator.register_hook(
        target_session_id=session_id,
        action_tool="mock_send_file_2",
        action_params={"to": "+923098956995", "path": "{worker.artifact}"},
        description="Send the generated file to Haseeb on WhatsApp",
    )

    bus = get_event_bus()

    # Mock WorkerSession SESSIONS_ROOT
    monkeypatch.setattr("app.workers.base.session.WorkerSession.SESSIONS_ROOT", tmp_path)
    session_dir = tmp_path / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "task.json").write_text(f'{{"objective": "Create the file in D:/workspace", "fs_scope": "{str(tmp_path).replace("\\", "/")}"}}')

    # Emit WORKER_COMPLETED with empty artifacts
    completion_evt = JarvisEvent(
        event_type=EventType.WORKER_COMPLETED,
        source=f"worker:{session_id}",
        title="Worker Completed",
        summary="Done",
        data={
            "session_id": session_id,
            "success": True,
            "artifacts": [],
            "output": {},
        },
    )
    bus.publish(completion_evt)

    await asyncio.sleep(0.1)

    assert len(mock_tool.executed_calls) == 1
    call = mock_tool.executed_calls[0]
    assert call["to"] == "+923098956995"
    assert str(ws_file.name) in call["path"]


@pytest.mark.asyncio
async def test_task_orchestrator_multi_worker_pipeline_chaining(monkeypatch):
    mock_tool = MockWhatsAppTool()
    mock_tool.name = "mock_send_file_3"
    registry.register(mock_tool)

    orchestrator = TaskOrchestrator()
    orchestrator.start()

    # Worker 1 session
    w1_session_id = "ws_worker_1"
    w2_session_id = "ws_worker_2"

    # Mock _fork_task
    async def fake_fork(params, prompt):
        return {
            "success": True,
            "data": {"session_id": w2_session_id, "status": "running"},
        }

    monkeypatch.setattr("app.api.routes.agent._fork_task", fake_fork)

    # Register Step 2 (worker 2) on Worker 1, with Step 3 (mock_send_file_3) in downstream_steps
    orchestrator.register_hook(
        target_session_id=w1_session_id,
        action_tool="fork",
        action_params={"objective": "Add quotations to haseeb.txt"},
        description="Fork second worker",
        downstream_steps=[
            {"tool": "mock_send_file_3", "params": {"to": "+923098956995", "path": "D:/workspace/haseeb.txt"}, "description": "Send via WhatsApp"}
        ],
    )

    bus = get_event_bus()

    # 1. Complete Worker 1
    bus.publish(
        JarvisEvent(
            event_type=EventType.WORKER_COMPLETED,
            source=f"worker:{w1_session_id}",
            title="Worker 1 Completed",
            summary="Done",
            data={"session_id": w1_session_id, "success": True, "artifacts": ["D:/workspace/haseeb.txt"]},
        )
    )

    await asyncio.sleep(0.1)

    # Worker 2 should now have Step 3 registered as its pending hook
    pending_w2 = orchestrator.get_pending_hooks(w2_session_id)
    assert len(pending_w2) == 1
    assert pending_w2[0].action_tool == "mock_send_file_3"

    # 2. Complete Worker 2
    bus.publish(
        JarvisEvent(
            event_type=EventType.WORKER_COMPLETED,
            source=f"worker:{w2_session_id}",
            title="Worker 2 Completed",
            summary="Done",
            data={"session_id": w2_session_id, "success": True, "artifacts": ["D:/workspace/haseeb.txt"]},
        )
    )

    await asyncio.sleep(0.1)

    # Mock send file tool should have been called!
    assert len(mock_tool.executed_calls) == 1
    call = mock_tool.executed_calls[0]
    assert call["to"] == "+923098956995"
    assert "haseeb.txt" in call["path"]


@pytest.mark.asyncio
async def test_task_orchestrator_interpolates_email_attachments():
    class MockSendEmailTool(BaseTool):
        name = "mock_send_email"
        description = "Mock send email tool"
        risk = RiskLevel.LOW
        category = "tool"
        input_schema = {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "attachments": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["to", "body"],
        }

        def __init__(self):
            super().__init__()
            self.executed_calls = []

        async def execute(self, params: dict) -> dict:
            self.executed_calls.append(params)
            return {"status": "sent", "to": params["to"], "attachments": params.get("attachments", [])}

    email_tool = MockSendEmailTool()
    registry.register(email_tool)

    orchestrator = TaskOrchestrator()
    orchestrator.start()

    session_id = "ws_email_chain_test"
    hook = orchestrator.register_hook(
        target_session_id=session_id,
        action_tool="mock_send_email",
        action_params={
            "to": "haseebhamza789@gmail.com",
            "subject": "Your File",
            "body": "Hi, please find attached {worker.artifact}",
            "attachments": ["{worker.artifact}"],
        },
        description="Send the generated file to Haseeb's email",
    )

    bus = get_event_bus()
    bus.publish(
        JarvisEvent(
            event_type=EventType.WORKER_COMPLETED,
            source=f"worker:{session_id}",
            title="Worker Completed",
            summary="Done",
            data={
                "session_id": session_id,
                "success": True,
                "artifacts": ["D:/workspace/haseeb_report.pdf"],
                "output": "Report generated",
            },
        )
    )

    await asyncio.sleep(0.1)

    assert len(email_tool.executed_calls) == 1
    call = email_tool.executed_calls[0]
    assert call["to"] == "haseebhamza789@gmail.com"
    assert call["attachments"] == ["D:/workspace/haseeb_report.pdf"]
    assert "D:/workspace/haseeb_report.pdf" in call["body"]


@pytest.mark.asyncio
async def test_task_orchestrator_multi_step_follower_pipeline():
    class MockSendEmailTool(BaseTool):
        name = "mock_pipeline_email"
        description = "Mock email"
        risk = RiskLevel.LOW
        category = "tool"
        input_schema = {"type": "object", "properties": {"to": {"type": "string"}, "attachments": {"type": "array"}}, "required": ["to"]}

        def __init__(self):
            super().__init__()
            self.calls = []

        async def execute(self, params: dict) -> dict:
            self.calls.append(params)
            return {"sent": True, "to": params.get("to"), "attachments": params.get("attachments", [])}

    class MockDriveTool(BaseTool):
        name = "mock_pipeline_drive"
        description = "Mock drive"
        risk = RiskLevel.LOW
        category = "tool"
        input_schema = {"type": "object", "properties": {"file_path": {"type": "string"}, "name": {"type": "string"}}}

        def __init__(self):
            super().__init__()
            self.calls = []

        async def execute(self, params: dict) -> dict:
            self.calls.append(params)
            return {"success": True, "file_id": "mock_drive_id_123", "name": params.get("name")}

    email_tool = MockSendEmailTool()
    drive_tool = MockDriveTool()
    registry.register(email_tool)
    registry.register(drive_tool)

    orchestrator = TaskOrchestrator()
    orchestrator.start()

    session_id = "ws_multi_step_follower"
    orchestrator.register_hook(
        target_session_id=session_id,
        action_tool="mock_pipeline_email",
        action_params={"to": "haseebhamza789@gmail.com", "attachments": ["{worker.artifact}"]},
        description="Email file to Haseeb",
        downstream_steps=[
            {
                "tool": "mock_pipeline_drive",
                "params": {"file_path": "{worker.artifact}"},
                "description": "Upload to Google Drive",
            }
        ],
    )

    bus = get_event_bus()
    bus.publish(
        JarvisEvent(
            event_type=EventType.WORKER_COMPLETED,
            source=f"worker:{session_id}",
            title="Worker Completed",
            summary="Done",
            data={
                "session_id": session_id,
                "success": True,
                "artifacts": ["D:/workspace/document.txt"],
                "output": "Document created successfully.",
            },
        )
    )

    await asyncio.sleep(0.1)

    # 1. Email tool executed with artifact
    assert len(email_tool.calls) == 1
    assert email_tool.calls[0]["to"] == "haseebhamza789@gmail.com"
    assert email_tool.calls[0]["attachments"] == ["D:/workspace/document.txt"]

    # 2. Drive tool executed with artifact
    assert len(drive_tool.calls) == 1
    assert drive_tool.calls[0]["file_path"] == "D:/workspace/document.txt"
    assert drive_tool.calls[0]["name"] == "document.txt"

    # 3. All hooks registered for session are marked executed
    hooks = orchestrator.get_hooks(session_id)
    assert len(hooks) == 2
    assert all(h.executed for h in hooks)




