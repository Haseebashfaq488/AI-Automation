# Adding New Modules to the Jarvis Backend

This guide explains how to add a new module (e.g., `gmail`, `calendar`, `drive`) that follows the same patterns as the existing `file_management` module. The module is organized into four sub‑packages: `skills`, `tools`, `pipelines`, and `helpers`. All components are registered in a central `ToolRegistry` and exposed via FastAPI routes.

---

## 1. Module skeleton

Create a directory under `backend/app/modules/<module_name>/` with the following layout:

```
modules/<module_name>/
├── __init__.py                # empty (or imports for convenience)
├── skills/
│   ├── __init__.py            # empty
│   └── <skill_name>.py        # BaseTool subclass (category == "skill")
├── tools/
│   ├── __init__.py            # empty
│   └── <tool_name>.py         # BaseTool subclass (category == "tool")
├── pipelines/
│   ├── __init__.py            # empty
│   └── <pipeline_name>.py    # orchestrates skills/tools via ExecutionEngine
└── helpers/
    ├── __init__.py            # empty
    └── validation.py           # reusable validation functions
```

### Minimal skill example (`skills/list_recent_emails.py`)

```python
from typing import Dict, Any
from app.core.tool import BaseTool, RiskLevel

class ListRecentEmailsSkill(BaseTool):
    name = "list_recent_emails"
    description = "List recent emails matching a search query."
    risk = RiskLevel.LOW
    category = "skill"
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "default": "in:inbox"},
            "max_results": {"type": "integer", "default": 10},
        },
        "required": [],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: integrate with real Gmail API
        return {"listed": True, "query": params["query"], "emails": []}
```

### Minimal tool example (`tools/send_email_tool.py`)

```python
from typing import Dict, Any
from app.core.tool import BaseTool, RiskLevel

class SendEmailTool(BaseTool):
    name = "send_email"
    description = "Send an email via Gmail API (optional file attachments)."
    risk = RiskLevel.MEDIUM
    input_schema = {
        "type": "object",
        "properties": {
            "to": {"type": "string"},
            "subject": {"type": "string", "default": ""},
            "body": {"type": "string"},
            "attachments": {"type": "array", "items": {"type": "string"}, "default": []},
        },
        "required": ["to", "body"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: call Gmail API
        return {"sent": True, "to": params["to"], "subject": params.get("subject", "")}
```

### Minimal pipeline example (`pipelines/list_recent_emails_pipeline.py`)

```python
from typing import Dict, Any
from app.core.execution_engine import ExecutionEngine
from app.registry import registry
from app.modules.gmail.skills.list_recent_emails import ListRecentEmailsSkill

class ListRecentEmailsPipeline:
    def __init__(self):
        self.engine = ExecutionEngine(registry)

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.engine.run(ListRecentEmailsSkill.name, params)
        return {
            "pipeline": "list_recent_emails",
            "success": result.success,
            "result": result.data,
            "error": result.error,
        }
```

### Helper example (`helpers/validation.py`)

```python
def validate_email_address(email: str) -> bool:
    return "@" in email and "." in email.split("@")[-1]


def validate_query(query: str) -> bool:
    return bool(query and query.strip())
```

---

## 2. Register the new components

All tools and skills must be registered in the **global `ToolRegistry`** so the execution engine can find them.

### Registry file (`app/registry/__init__.py`)

Add import lines and register instances, following the existing pattern:

```python
# Gmail module
from app.modules.gmail.tools.send_email_tool import SendEmailTool
from app.modules.gmail.skills.list_recent_emails import ListRecentEmailsSkill

registry.register(SendEmailTool())
registry.register(ListRecentEmailsSkill())
```

> **Do not modify `lifecycle.py`** unless you need to add database initialization; the registry is standalone.

---

## 2b. Make the tool available to the AGENT (essential!)

Registering a tool in the registry (step 2) exposes it via `/tools/run/...`, but
the **LLM agent will never plan with it** unless you also add it to the adapter's
known-tools list. This is the step people forget — the symptom is the agent
replying *"I'm not sure what you'd like me to do"* to requests that should work.

### Adapter file: `app/modules/opencode/adapter.py`

Add your tool to `OpenCodeAdapter._KNOWN_TOOLS` with a param doc for **every**
schema property (one-line descriptions, marking optional ones):

```python
_KNOWN_TOOLS = {
    # ... existing entries ...
    "send_email": {
        "to": "recipient email address",
        "subject": "optional email subject (omit for no subject)",
        "body": "email body text",
        "attachments": "optional list of absolute file paths to attach to the email",
    },
}
```

### Rules that bite if ignored

- **Unknown tool = silently dropped.** `_validate_plan_steps()` drops any step
  whose tool is not in `_KNOWN_TOOLS`. If *all* steps of a plan are dropped, the
  agent asks the user for the missing info instead of executing.
- **Param docs must match `input_schema`.** Required params (per the registered
  schema) must be present **and non-empty** in the plan or the step is dropped.
  If a param should be optional, give it a `default` in `input_schema`, document
  it as "optional" here, and never list it in `required`.
- **Fallback required-params.** When no registry is attached to the adapter,
  `_required_params()` falls back to "every documented param except the known
  optionals set". Prefer running with the registry (the `/agent` route does) so
  the tool's real schema drives validation.
- **Prompt scope.** The planning system prompt is general-purpose (files +
  WhatsApp + email). If you add a whole new capability class, extend the prompt
  text in `_planning_system_prompt()` — do not narrow it back to file ops.
- **Restart required** — the adapter and registry are loaded at app startup;
  restart the backend after editing either.

### Verify the agent can plan with the new tool

```powershell
curl -X POST http://localhost:8000/agent/run -H "Content-Type: application/json" `
  -d '{"prompt": "<a request that should use your new tool>", "session_id": "smoke"}'
# expect: {"mode": "plan", "steps": [{"tool": "<your_tool>", ...}]}
```

---

## 3. Expose the module via the API

### 3.1 Tools endpoint

The router at `app/api/routes/tools.py` already provides:

- `GET /tools/list` → lists all registered tools (name, description, risk, category)
- `POST /tools/run/{tool_name}` → executes a tool by name with JSON parameters

No code change is needed; just registering the tool in the registry is sufficient.

### 3.2 Pipelines endpoint

Edit `app/api/routes/pipelines.py` to import and add the new pipeline to the static `pipelines` dictionary:

```python
from app.modules.gmail.pipelines.list_recent_emails_pipeline import ListRecentEmailsPipeline

router = APIRouter(prefix="/pipelines", tags=["pipelines"])

pipelines = {
    # ... existing entries ...
    "list_recent_emails": ListRecentEmailsPipeline(),
}
```

Now the following endpoints are available:

- `GET /pipelines/list` → returns pipeline names
- `POST /pipelines/run/{pipeline_name}` → runs the pipeline

---

## 4. Optional: Add helper imports

If the module provides useful validation or path‑resolution helpers, they can be imported from `app.modules.<module_name>.helpers`. Example usage in other code:

```python
from app.modules.gmail.helpers.validation import validate_email_address
```

---

## 5. Quick checklist

| Step | What to do |
|------|------------|
| **Create directory** | `backend/app/modules/<module_name>/skills/`, `tools/`, `pipelines/`, `helpers/` |
| **Write skill** | Subclass `BaseTool`, set `category = "skill"` |
| **Write tool** | Subclass `BaseTool`, set `category = "tool"` |
| **Write pipeline** | Create class that uses `ExecutionEngine.run(skill_name, params)` |
| **Write helpers** (optional) | Plain functions for validation, path resolution, etc. |
| **Register** | Add imports + `registry.register(...)` in `app/registry/__init__.py` |
| **Wire pipelines** | Import + add to `pipelines` dict in `app/api/routes/pipelines.py` |
| **Wire the agent** | Add the tool + param docs to `_KNOWN_TOOLS` in `app/modules/opencode/adapter.py` (see §2b) |
| **Test** | `curl http://localhost:8000/tools/list` and `curl -X POST http://localhost:8000/tools/run/<tool> ...` |
| **Agent smoke test** | POST an agent prompt that should plan with the new tool; confirm `"mode": "plan"` |
| **Docs** | Append a session entry to `backend/IMPLEMENTATION_LOG.md`; update `AGENTS.md` if conventions changed |

---

## 6. Conventions to keep in sync

- **`BaseTool` attributes**: `name` (unique string), `description`, `risk` (`RiskLevel.LOW/MEDIUM/HIGH`), `category` (`"tool"` or `"skill"`), `input_schema` (JSON‑schema dict).
- **`execute`**: `async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]` – the engine calls this after schema validation.
- **Naming**: Use snake_case for file names and class names (e.g., `send_email_tool.py`, `SendEmailTool`).
- **Risk level**: `LOW` for read‑only/list operations, `MEDIUM` for write operations, `HIGH` for destructive actions.
- **Documentation**: Add a brief docstring to each class describing parameters and return shape.

---

## 7. Write unit tests

All new tools and pipelines should have corresponding unit tests placed in the
backend test directory. The project uses `pytest` (and `pytest-asyncio` for async
code). Tests live under `backend/tests/` and are organized by module, e.g.:

```
backend/tests/
├── test_gmail_tools.py
├── test_gmail_pipelines.py
└── ...
```

### Testing a tool

```python
# backend/tests/test_gmail_tools.py
import pytest
from app.core.execution_engine import ExecutionEngine
from app.registry import registry
from app.modules.gmail.tools import send_email_tool
from app.modules.gmail.tools.send_email_tool import SendEmailTool

@pytest.fixture(autouse=True)
def setup_registry(monkeypatch):
    registry.register(SendEmailTool())
    # Force the "no credentials" path so tests never depend on (or touch) a
    # real token.json or external API. Patch the module-level lookup.
    monkeypatch.setattr(send_email_tool, "_load_token_path", lambda: None)
    yield

async def test_send_email_missing_params():
    engine = ExecutionEngine(registry)
    with pytest.raises(Exception):
        await engine.run("send_email", {"to": "a@b.com"})  # body is required

async def test_send_email_mock_mode(monkeypatch, tmp_path):
    # GMAIL_MOCK=1 makes the tool return simulated success — no network.
    monkeypatch.setenv("GMAIL_MOCK", "1")
    f = tmp_path / "report.txt"
    f.write_text("data")
    engine = ExecutionEngine(registry)
    result = await engine.run("send_email", {
        "to": "test@example.com", "subject": "s", "body": "b",
        "attachments": [str(f)],
    })
    assert result.success == True
    assert result.data["attachments"] == ["report.txt"]
```

> **Credential independence rule:** any test for a tool that talks to an
> external API must mock/patch the credential lookup (as above) so the test
> suite passes identically with or without a real `token.json` on disk.
> Use `GMAIL_MOCK=1` (or your module's equivalent) for happy-path coverage.

### Testing a pipeline

```python
# backend/tests/test_gmail_pipelines.py
import pytest
from app.registry import registry
from app.modules.gmail.pipelines.list_recent_emails_pipeline import ListRecentEmailsPipeline

@pytest.fixture(autouse=True)
def setup_pipeline():
    # the pipeline is already wired in routes; just ensure skill is registered
    from app.modules.gmail.skills.list_recent_emails import ListRecentEmailsSkill
    registry.register(ListRecentEmailsSkill())
    yield

def test_list_recent_emails_pipeline():
    pipeline = ListRecentEmailsPipeline()
    # execute with empty params (skill returns empty list)
    result = pytest.asyncio.run(pipeline.run({}))
    # result is a dict as returned by pipeline.run()
    assert isinstance(result, dict)
    # You can assert "success" key etc. depending on your implementation
```

### Running the tests

From the backend directory:

```powershell
cd backend
pytest
```

or to run only the new module tests:

```powershell
cd backend
pytest tests/unit/test_gmail_tools.py tests/unit/test_gmail_pipelines.py
```

Make sure every `execute` method and `run` method has at least one test covering:

* valid input → success with expected data
* missing required parameters → failure / error response
* invalid input types → validation error (the engine raises before `execute`)

Keeping test files under version control and running them as part of CI ensures that new modules do not break existing functionality.
---

Now you can add as many modules as needed, and they’ll be automatically discoverable via the `/tools/list` and `/pipelines/list` endpoints, just like `file_management` and the newly added `gmail` module.