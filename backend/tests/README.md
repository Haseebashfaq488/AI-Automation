# `tests/` — Backend Automated Test Suite

## 1. Directory Role & Boundary
The `tests/` directory contains all unit, integration, and contract tests for the Jarvis backend. Tests validate tool implementations, reactive orchestrators, two-phase agent cycles, worker contracts, and session handover synthesis.

---

## 2. Test Suite Inventory (`tests/unit/`)
| Test File | Focus Area | What It Validates |
| :--- | :--- | :--- |
| [`test_session_handover.py`](file:///d:/AI-Automation/backend/tests/unit/test_session_handover.py) | Handover & Continuity | Subfolder living doc scanning, handover synthesis, dynamic `fs_scope` resolution, and `GET /workers/{id}/handover` endpoint. |
| [`test_task_orchestrator.py`](file:///d:/AI-Automation/backend/tests/unit/test_task_orchestrator.py) | Reactive Pipelines | Downstream hook execution, dynamic attachment extraction from worker artifacts, and email/drive chaining. |
| [`test_agent_fork.py`](file:///d:/AI-Automation/backend/tests/unit/test_agent_fork.py) | Task Forking | Two-phase agent `/agent/run` plan generation and `fork` pseudo-tool background delegation. |
| [`test_antigravity_brain.py`](file:///d:/AI-Automation/backend/tests/unit/test_antigravity_brain.py) | Brain Orchestration | Semantic tool index retrieval, plan generation, and memory extraction. |
| [`test_memory_vector_index.py`](file:///d:/AI-Automation/backend/tests/unit/test_memory_vector_index.py) | Semantic Memory Retrieval | Ultra-low latency ONNX vector retrieval, lexical keyword boosting, and greeting bypass. |
| [`test_onnx_embedder.py`](file:///d:/AI-Automation/backend/tests/unit/test_onnx_embedder.py) | ONNX Runtime Embedder | Single/batch encoding, 384-dim normalized vector validation, and singleton lifecycle. |
| [`test_antigravity_worker.py`](file:///d:/AI-Automation/backend/tests/unit/test_antigravity_worker.py) | Worker Execution | Multi-job milestone prompts, CLI client subprocess invocation, and output parsing. |
| [`test_drive_tools.py`](file:///d:/AI-Automation/backend/tests/unit/test_drive_tools.py) | Google Drive Module | List, search, read, and upload Drive tools (mock & live paths). |
| [`test_file_tools_v2.py`](file:///d:/AI-Automation/backend/tests/unit/test_file_tools_v2.py) | File Management | 11 file tools, protected directory refusal, trash deletion, and zip archives. |
| [`test_events_route.py`](file:///d:/AI-Automation/backend/tests/unit/test_events_route.py) | Event Bus Routes | SSE event streaming and hook registration endpoints. |
| [`test_plan_review_and_skip_testing.py`](file:///d:/AI-Automation/backend/tests/unit/test_plan_review_and_skip_testing.py) | Plan Reviews & Verification Skip | Plan revision requests routing back to Job 1, edited markdown propagation to `fs_scope`, and skip testing bypassing Job 3. |
| [`test_frontend_integration.py`](file:///d:/AI-Automation/backend/tests/unit/test_frontend_integration.py) | End-to-End Contract | Full integration flow simulating frontend API calls. |

---

## 3. Running Tests
Run all unit tests using pytest from `backend/`:

```powershell
# Run the complete unit test suite
pytest tests/unit/

# Run a specific test suite
pytest tests/unit/test_session_handover.py -v

# Run with stdout printing enabled
pytest tests/unit/ -s
```

---

## 4. Testing Conventions & Mocking
* **Isolation from Live External APIs**: Tests covering Gmail or Google Drive must never fail due to missing local OAuth tokens. Always monkeypatch `_load_token_path -> None` or set `GMAIL_MOCK=1` / `DRIVE_MOCK=1`.
* **Async Testing**: All asynchronous test functions use `@pytest.mark.asyncio` with the `asyncio_mode = "auto"` configuration in `pyproject.toml`.
* **Temporary Directories**: Use pytest's `tmp_path` fixture for any test that creates files or test directories to keep the workspace clean.
