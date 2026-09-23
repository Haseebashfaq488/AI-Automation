# Jarvis Backend Implementation Log

---

## ✅ Completed Modules

### Module 1 – Backend Foundation & Core Config
- Project scaffold (`backend/`), dependencies (`requirements.txt`), build config (`pyproject.toml`).
- Environment files (`.env.example`, `.env`).
- Core config (`app/core/config.py`), structured logging (`app/core/logging.py`).
- Exception hierarchy (`app/core/exceptions.py`).
- Application lifecycle (`app/core/lifecycle.py`).
- FastAPI entry point (`app/main.py`).
- Health endpoint (`app/api/routes/health.py`).
- Tests (`tests/conftest.py`, `tests/unit/test_health.py`).

### Module 2 – Core Tool System & Execution Engine
- Abstract tool contract (`app/core/tool.py`) with `BaseTool`, `RiskLevel`, and `category`.
- `ToolResult` model (`app/core/tool_result.py`).
- `ToolRegistry` (`app/registry/tool_registry.py`) with global registry instance.
- Execution engine (`app/core/execution_engine.py`) with required-param validation.

## 📁 Module Structure

```
app/modules/
├── database/                  # SQLite persistence (tasks, execution logs)
├── file_management/           # All file-management capabilities
│   ├── helpers/               # paths, validation (protected paths), verification
│   ├── tools/                 # 11 low-level file tools (read-only + mutation + dry-run)
│   ├── skills/                # Higher-level skills (e.g. organize_downloads)
│   └── pipelines/             # Pipelines orchestrating skills/tools
└── opencode/                  # Groq LLM adapter (prompt → plan)
```

### Module 3 – File System Safety & Path Helpers
- Path resolver (`app/modules/file_management/helpers/paths.py`).
- Validation helpers (`app/modules/file_management/helpers/validation.py`) — protected paths enforced by all mutation tools.
- Verification helpers (`app/modules/file_management/helpers/verification.py`).

### Module 4 – Read-Only File System Tools
- `list_directory`, `exists`, `metadata`, `search_files` (glob `pattern`), `read_file` (10 MB size guard), `search_content` (grep-like text search with line numbers, binary/large-file skip).

### Module 5 – Mutation Tools & Dry-Run Engine
- `create_file`, `create_folder`, `write_file`, `copy`, `move`, `rename`.
- Extended set: `delete_file` / `delete_folder` (HIGH risk — recoverable trash by default, `permanent=true` to destroy), `archive` / `extract` (zip + zip-slip protection), `touch`, `bulk_rename` (`#` counter patterns), `append_file`.
- All support `dry_run`; all enforce protected-path validation; `rename` uses `shutil.move` (Windows-safe overwrites).
- Registered in the global registry.

### Module 6 – Database, Task Manager & Execution Journal
- Persistent SQLite database via SQLAlchemy (`app/modules/database/`).
- ORM models `Task` and `ExecutionLog` (timezone-aware timestamps).
- Repository layer with CRUD and logging methods.
- `/tasks` endpoints enabled (list / create / get / patch).

### Module 7 – OpenCode (Groq) Integration Adapter
- `OpenCodeAdapter` (`app/modules/opencode/adapter.py`) — async Groq chat-completion client.
- Two-phase planning: `analyze_prompt` returns a direct response or a validated plan.
- Plan steps are validated against each tool's real `input_schema`; invalid steps are dropped.
- Adapter tool docs match actual tool schemas exactly (fixed `search_files.pattern`, `rename.source/destination`, `organize_downloads.source_dir`).
- Lazy initialization in `/agent` route — the app boots even when `GROQ_API_KEY` is missing (503 on use instead of crash).

### Module 8 – File System Skills & Pipelines
- `OrganizeDownloadsSkill` (`app/modules/file_management/skills/organize_downloads.py`) — organizes a directory by extension; `category = "skill"`.
- Pipelines (`app/modules/file_management/pipelines/`): `organize_downloads`, `organize_photos` (YYYY/MM), `dedupe_folder` (SHA-256 review), `backup_documents` (incremental), `archive_old_files` (zip + remove), `sort_by_date` (YYYY-MM). All support `dry_run`.

### Module 10 – Agent Memory
- Short-term **chat memory** (`app/modules/memory/chat_memory.py`): per-session sliding window (20 msgs) injected into the Groq messages array; view/clear via `/agent/history`.
- Long-term **memory** (`app/modules/memory/long_term.py` + SQLite `memories` table): durable facts extracted after each agent turn via a dedicated LLM call, deduped, capped (100), injected into the planning prompt; view/clear via `/agent/memory`.
- `PromptRequest` gained `session_id` (default `"default"`); both memory layers are per-session aware.
- Endpoints: `GET/DELETE /agent/memory`, `GET/DELETE /agent/history`.

### Module 9 – API Layer, Event Streaming & End-to-End Validation
- Routers: `/tools`, `/skills` (skills only), `/pipelines`, `/tasks`, `/agent`, `/events`.
- SSE endpoint `/events/stream` enabled.
- Full end-to-end validation done (all tools, skills, pipelines, tasks, agent two-phase flow with real Groq).

---

## 📋 Workflow Overview
1. Client POST `/agent/run` with a natural-language prompt.
2. `OpenCodeAdapter.analyze_prompt` asks Groq for a JSON plan (or direct response).
3. Plan steps are validated against the registry schemas; a `plan_id` is returned for user review.
4. Client POST `/agent/run` with `confirm=true` + `plan_id` → steps execute sequentially via `ExecutionEngine`.
5. Each step returns a `ToolResult` (success, data, error); the agent route aggregates them.

### Verified end-to-end flows
- create_file → write_file via real LLM plan ✅
- search_files `*.txt` via real LLM plan ✅ (regression-tested)
- conversational prompt → direct response ✅
- mutation CRUD, dry-run, protected-path refusal, tasks CRUD, SSE stream ✅
- new tools: search_content, touch, append_file, bulk_rename, archive/extract roundtrip, delete-to-trash ✅
- pipelines: organize_photos, dedupe_folder, backup_documents (incremental), archive_old_files, sort_by_date ✅
- agent memory: fact learned in turn 1, recalled in turn 2 via `/agent/memory` injection ✅
- `pytest -q` → **47 passed**

---

## Session: Optimizing the WhatsApp DOM Feature (2026-09-11)

### Context
- whatsapp-web.js (1.26→1.34.7 incl. master) and venom-bot 5.3.0 both abandoned → replaced by our **own Puppeteer DOM driver** (`backend/whatsapp_service/server.js`, port 4097) running against a **copied Chrome profile** (`chrome_profile_copy/`, synced via `sync_profile.ps1`; Chrome must be closed during sync). Chrome v153 blocks `--remote-debugging-port` on the real user-data dir, hence the copy.
- Session is pre-authenticated (logged in as the user, `pushname` from profile `Default`) — no QR flow in practice.
- Backend contract unchanged: FastAPI tools → `helpers/client.py` singleton → sidecar REST. Python tests monkeypatch `get_client()` with `FakeWhatsAppClient`.

### Root causes found & fixed (live debugging against real WhatsApp Web)
1. **Search box not found** — WhatsApp replaced the contenteditable search div with a plain `<input class="html-input" aria-label="Search or start a new chat">` inside `div[data-testid="chat-list-search-container"]`.
2. **Keystrokes lost while searching** — React re-renders the controlled input on each keystroke and drops focus (`keyboard.type` only landed "+92"). Fix: set value via native `HTMLInputElement.prototype.value` setter + dispatch `input` event.
3. **Search result click did nothing** — JS `.click()` doesn't trigger navigation; results are `[data-testid="cell-frame-container"]` without `role="listitem"`. Fix: exact-then-substring title match, real element-handle click, `waitForSelector("#main")`.
4. **Self/phone chats unsearchable** — own number doesn't surface in search at all. Fix: phone-like chats (`phoneDigits()` ≥7 digits) route via `web.whatsapp.com/send?phone=<digits>` URL instead of search (applies to `/messages`, `/send`, `/send-file`).
5. **`send_file` silently failed** — current WA Web has **no document `<input>` in the DOM** (only a permanent hidden `image/*` one; `showOpenFilePicker` not used either; synthetic DragEvent drop ignored — WA gates on trusted events). Uploading a `.txt` to the image input triggered "1 file you tried adding is not supported". Fix: click attach → click "Document"/"Photos & videos" menu item → intercept the **native file chooser** (`page.waitForFileChooser()` + `chooser.accept([path])`); WA creates the input dynamically at menu-click time and removes it when the dialog closes.
6. **`fromMe` always false** — tick icons lost stable `data-testid`s. Fix: positional detection (outgoing bubbles hug the right edge of `#main`, gap ≈57px vs ≥300px for incoming; threshold 120px).
7. **Message scraping** — bubbles are now `[data-testid="msg-container"]` (old `div.message-in/out` gone); text via `.selectable-text(.copyable-text)`.

### Verified live (through backend `:8000`, all ✅)
- `whatsapp_status`, `list_chats` (8 real chats), `send_message`, `get_messages` (correct bodies + `fromMe`), `send_file` (document + caption confirmed delivered in self-chat `+923098956995`).
- Full stack: frontend `:3000`, backend `:8000`, sidecar `:4097` all running.
- Cleanup: temporary `/probe*` routes removed, per-run debug screenshots removed (failure-path screenshots kept: `dbg_search_fail.png`, `dbg_chat_open_fail.png`, `dbg_send_fail.png`).

### Known limitations
- `list_contacts`, `get_chat_info`, `manage_chat`, `manage_group`, `download_media` → backend tools registered but sidecar returns **501** (contract-compatible stubs until implemented).
- Speed: `send_message` ≈10–20 s, `send_file` ≈30–45 s (boot 30–45 s per restart) — dominated by per-message `page.goto()` full reloads, fixed `sleep()` padding, and serialized queue.

### Optimization plan (accepted next steps, not yet implemented)
1. **Persistent Chrome**: start Chrome once with `--remote-debugging-port`; sidecar uses `puppeteer.connect()` → instant restarts, boot paid once.
2. **Reuse open chat** instead of `page.goto` per message (SPA, no reloads when target unchanged).
3. **Condition waits** (`waitForSelector`/`waitForFunction`) replace fixed sleeps.
4. **Request interception** to block images/media → lighter page.
- Target: send ≈2–4 s, send_file ≈5–8 s.
- Alternatives considered: Baileys (WS protocol — fast but requires fresh QR pairing + ban risk), official WhatsApp Business API (paid) — both deferred.

---

## Session: Gmail Tools, OAuth & Agent Email Routing (2026-09-12)

### Tested & fixed end-to-end (all ✅)
- **OAuth token wiring bug**: `setup_gmail_oauth.py` saved `token.json` to `D:\GmailAssistant\` but the tools read `backend/token.json` (or module-local) — token was invisible. Fixed the script (saves to `backend/token.json`, requests combined scopes) and copied the existing token into place.
- **Scope split**: original token had only `gmail.send`; `list_recent_emails` needs `gmail.readonly`. Both tools/skill now request both scopes and **persist refreshed tokens back to `token.json`**. User re-ran the OAuth flow to grant readonly.
- **Agent "not sure what file operation you need" bug**: root cause was in `opencode/adapter.py` — the planning prompt declared Jarvis a *file-system assistant* and told the LLM to treat non-file prompts as chitchat, so email requests never became plans; the fallback message was file-specific. Fixed: general-purpose prompt (files + WhatsApp + email), generic fallback message. Also fixed in the legacy single-step prompt.
- **`list_recent_emails` required `query`** — "list my recent emails" has no natural query, so valid LLM plans were dropped by plan validation. `query` is now optional (defaults to `in:inbox`); adapter docs updated.
- **Gmail tests env-dependence**: 3 tests assumed no `token.json` exists; now monkeypatch `_load_token_path → None` to force the no-credentials path deterministically.

### Verified live via backend (:8000)
- `POST /tools/run/send_email` — real Gmail send ✅ (delivery failure notices from `test@example.com` prove it left the outbox)
- `POST /skills/run/list_recent_emails` — real inbox listing ✅
- `POST /pipelines/run/list_recent_emails` — pipeline → skill ✅
- Agent: "send an email…" → plans `send_email` → confirm → sent ✅; "check my inbox…" → plans `list_recent_emails` → confirm → lists ✅
- `pytest -q` → **74 passed** (was 70, +3 gmail tests now env-independent… net 74 with 4 new gmail/agent tests)

### State
- `backend/token.json` holds the live OAuth token (send + readonly); auto-refreshes and persists on expiry.
- To re-auth: `python setup_gmail_oauth.py` (browser flow), token saved to `backend/token.json`.

### Addendum: attachments + agent robustness (same day)
- **`send_email` supports attachments**: optional `attachments` list of absolute paths;
  files validated/read before any Gmail call (fail fast on missing path or >25 MB total);
  MIME type via `mimetypes`; `EmailMessage.add_attachment` → multipart/mixed.
  Verified live: email with .txt attachment delivered to haseebhamza789@gmail.com ✅;
  agent plans `attachments` correctly from natural language ✅.
- **Agent silent-drop fix**: `_validate_plan_steps` now returns `(valid, dropped)` with
  drop reasons; when a proposed plan loses all steps the agent replies with exactly what
  is missing (e.g. "send_email needs: subject") instead of a generic "not sure".
- `send_email.subject` made optional (was required; "without any subject" requests used
  to produce empty-subject plans that validation dropped).
- Tests: +attachment fail-fast, +mock-mode-with-attachment; adapter validation tests
  updated for the tuple return. `pytest -q` → **76 passed**.
- Docs: `ADDING_MODULES.md` gained §2b "Make the tool available to the AGENT"
  (`_KNOWN_TOOLS` wiring, silent-drop rules, credential-independent testing);
  stale `send_email`/`list_recent_emails` examples refreshed.
- Ops gotcha: backend started with default `uvicorn` spawns a **multiprocessing worker**
  that holds :8000 — killing only the parent leaves the port bound; kill worker PIDs too.

---

## Session: Worker / Orchestrator Architecture — Steps 0–1 (2026-09-12)

Implements the parent‑worker plan from `DESIGN_AND_PLAN_FOR_THE_NEXT_BIGGER_MODULE.md`.

### Step 0 — plumbing (done earlier same day)
- `app/workers/base/`: `TaskContract` (pydantic v2), `WorkerSession` (disk: task/state/events.jsonl/artifacts/logs/result under `worker_sessions/<id>/`), `EventBus` (module‑level pub/sub), `ScopedToolRegistry` (permission layer: only allow‑listed tools), `WorkerEngine` (fork → background loop → result; intervene/cancel).
- `app/api/routes/workers.py`: `/workers/fork`, `/list`, `/{id}`, `/{id}/result`, `/{id}/intervene`, `/{id}/cancel`, `/{id}/events` (SSE with replay).
- Frontend: `/workers` dashboard + `/worker/[id]` live page (forked chat, activity sidebar, intervene/cancel) — verified with `npx next build`.

### Step 1 — Word worker + worker LLM (this session)
- **6 word tools** (`app/workers/document_worker/word_worker/tools/`, all registered in the global registry):
  `inspect_docx`, `read_docx` (pagination), `normalize_headings` (`#`–`#####` → Heading 1–5),
  `fix_spacing`, `format_tables` (validated style names), `backup_docx`.
  Helpers in `word_worker/helpers/`: `resolve_doc_path` (fs_scope boundary + protected paths),
  `open/backup/save_docx` (save re‑opens to verify).
- **`DocumentWorkerAgent`** (`document_worker/agent/`): tiny scope‑locked system prompt
  (own objective + own step results only — never parent history), JSON decision protocol
  (`tool` / `done` / `fail`), LLM = OpenRouter `nvidia/nemotron-3.5-lightning:free` via the
  refactored `OpenCodeAdapter(base_url, api_key, model)`; `WORKER_MODEL`/`OPENROUTER_API_KEY`
  from `config.py`. No key → `available=False` → engine falls back to placeholder loop.
- **`WorkerEngine` now LLM‑driven**: `_agent_loop` (decide → execute → `record_step` → repeat;
  parent interventions injected as pseudo‑steps; max_steps hard cap; cooperative cancel) and
  `_placeholder_loop` (Step 0 behavior) share `_execute_step`/`_finalize` helpers. Agent is
  injected via `agent_factory` so `base` stays decoupled; `/workers/fork` passes a factory
  for `worker_type="document_worker"`.

### Bug fixes along the way
- `TaskContract.fs_scope` validator was POSIX‑only (`v.startswith("/")`) — Windows absolute
  paths (`C:\…`) rejected. Now `Path(v).is_absolute()` (+ missing `Path` import).
- Parent interventions weren't visible to the worker LLM: `decision_user_message` now renders
  step output (guidance text included) instead of just `ok`.
- Old worker tests hardcoded POSIX `/tmp`, `/` as `fs_scope` — switched to `os.path.abspath`.

### Verification
- `pytest -q` → **125 passed** (+13 word tools, +9 agent unit, +5 engine↔agent loop).
- Live smoke on temp uvicorn :8001 (main :8000 serves stale code, no `--reload`): fork with
  `worker_type="document_worker"` + word tools → placeholder mode ran the tools, failures
  reported cleanly through `/result` (no real .docx present — expected). Temp server killed,
  smoke session dir removed.

### Not yet done (next sessions)
- Step 2: Excel worker tools (`openpyxl` 3.1.5 already installed).
- Parent integration: `delegate_to_worker` pseudo‑tool in `_KNOWN_TOOLS` + `_execute_plan`
  interception, so the parent agent can spawn workers from chat.
- Artifacts download endpoint for the frontend worker page.

---

## Session: Fork UX — agent `fork` tool, manual fork form, chat persistence (2026-09-12)

### Agent can fork
- `fork` is now a pseudo‑tool in `OpenCodeAdapter._KNOWN_TOOLS` (planning prompt rule 2b:
  "fork"/"delegate"/"spawn a worker" → plan a `fork` step). Its params are all optional —
  `_required_params` falls back to the user's prompt when the LLM omits them.
- `_execute_plan` (agent.py) intercepts `tool == "fork"` **before** the tool registry and calls
  `_fork_task()`, which builds a `TaskContract` (defaults: word tools, fs_scope `D:\`,
  objective = user's words) and launches via `workers_routes.launch_worker()` — the same
  entry the `/workers/fork` route uses, so agent‑forked workers are instantly queryable and
  show `worker_url` in the chat result card.

### Worker sessions survive restarts
- `WorkerSession.__init__` contract is now optional; `workers.py` gained `_disk_sessions()`
  (scans `worker_sessions/*/task.json`). `GET /workers/list`, `/{id}`, `/{id}/result` fall
  back to disk when the engine is no longer in memory (backend restart). `launch_worker()`
  extracted as the shared fork entry point.

### Frontend
- **Chat persistence**: `page.js` restores messages from `sessionStorage` on reload
  (stuck "thinking" bubbles filtered) and saves on every change. **New Chat** button clears
  the UI, the stored copy, and server‑side chat history (`DELETE /agent/history`) — worker
  sessions untouched.
- **Manual fork form** on `/workers`: objective, fs_scope, tool checkboxes (6 word tools +
  `list_directory`/`exists`), max steps → POST `/workers/fork` → redirects to the live
  `/worker/[id]` page. This is the interim way to test forking without the agent.
- `ExecutionCard` renders a fork result as an "Open worker live" link.

### Worker LLM fix (found by live testing)
- First live agent run failed every step with `Missing required parameters: ['path']` —
  the agent didn't know which files existed in its scope. `DocumentWorkerAgent` now scans
  fs_scope for `*.docx` (≤2 levels deep) and injects "FILES ALREADY IN YOUR SCOPE (use these
  exact absolute paths)" into the system prompt, plus rule 6: always pass absolute paths.

### Verified live (temp uvicorn :8002, real OpenRouter key in `.env`)
- Agent‑mode fork: backup_docx → inspect_docx → normalize_headings → inspect_docx,
  `success: true`, report.docx `#`/`##` lines converted to real Heading 1/2, `.backup.docx`
  created first. Forking confirmed working.
- `pytest -q`: fork/disk/agent suites pass (full‑suite slowness with a real key in `.env` is
  a known leftover — tests that fork workers must monkeypatch `get_worker_api_key`).

---

## Session: Jarvis + OpenCode CLI Worker Architecture & Word Worker Removal (2026-09-15)

### Summary
- Replaced legacy Word Worker (`document_worker`, docx tools, python-docx dependency) with
  `OpenCodeWorkerAgent` — an autonomous coding worker that interfaces with the `opencode` CLI.
- Preserved the existing forking foundation (`WorkerEngine`, `WorkerSession`, `EventBus`,
  `TaskContract`, disk persistence, intervention queue, SSE streaming).

### Key Components Built
1. **`app.workers.opencode_worker` Package**:
   - `config.py`: Environment-driven resolution for `opencode` binary path, default model
     (`OPENCODE_MODEL`, default `opencode/gemini-3.5-flash-lite`), auto-approval flag (`OPENCODE_AUTO`),
     and execution timeout (`OPENCODE_MILESTONE_TIMEOUT`).
   - `milestones.py`: Deterministic 4-phase milestone decomposition:
     `Analyze` → `Implement` → `Test & Fix` → `Verify`. Builds structured milestone prompts
     with project directory, task requirements, constraints, success criteria, and parent interventions.
   - `cli_client.py`: Async subprocess client wrapping non-interactive `opencode run`. Streams JSON
     events, captures output, extracts and reuses session IDs (`--session`) across milestones for
     continuity, and supports timeouts and clean cancellation.
   - `worker_agent.py`: Implements `WorkerEngine`'s agent contract (`available`, `decide_next_step`,
     `record_step`, `inject_intervention`). Steps through the 4 milestones sequentially within a
     single persistent OpenCode session.
2. **Registry & Routing Wiring**:
   - Cleaned all docx tool registrations and imports from `app/registry/__init__.py`.
   - Updated `OpenCodeAdapter._KNOWN_TOOLS` in `app/modules/opencode/adapter.py` to remove docx tools
     and update the `fork` tool definition.
   - Updated `backend/app/api/routes/workers.py`: default `worker_type` is now `"opencode_worker"`,
     and `_agent_factory_for` instantiates `OpenCodeWorkerAgent`.
   - Updated `backend/app/api/routes/agent.py`: default fork tools changed to coding/file tools
     (`list_directory`, `read_file`, `write_file`, `create_file`, etc.).
3. **Frontend Updates**:
   - `frontend_routing/app/workers/page.js`: Updated tool options to file/coding tools, updated
     quick presets ("Implement Feature", "Refactor Module", "File Inspection"), and set
     `worker_type: "opencode_worker"`.
   - `frontend_routing/app/page.js`: Updated quick suggestion to "⚡ Fork Coding Task".
4. **Testing**:
   - Removed all legacy Word Worker tests (`test_word_worker.py`, `test_worker_agent*.py`).
   - Added comprehensive suite in `tests/unit/test_opencode_worker.py` (29 tests) covering config,
     milestones, prompt generation, CLI client arguments, session continuity, and agent decision loops.
   - Updated `test_agent_fork.py` and `test_workers_api.py` monkeypatches.
   - All 134 backend tests pass (100% green).

---

### Module 14 – Google Drive Integration & Unified Tooling
1. **Authentication & Client Management**:
   - `setup_drive_oauth.py`: OAuth 2.0 flow using Desktop Client credentials from `mcp_config.json` or `drive_client_secret.json`. Requests drive readonly, file, and metadata scopes and stores tokens to `drive_token.json`.
   - `app/modules/drive/helpers/drive_client.py`: Singleton credentials loader with automatic token expiration refresh (`google.auth.transport.requests.Request`), Google Docs export MIME conversion, and mock mode support (`DRIVE_MOCK=1`).
2. **Tools & Skills**:
   - `ListDriveFilesTool` (`list_drive_files`): Query files and folders with size formatting, metadata, and webViewLinks.
   - `ReadDriveFileTool` (`read_drive_file`): Read text or download files by file ID, supporting Google Docs automatic export and local file saving.
   - `UploadDriveFileTool` (`upload_drive_file`): Multipart file upload to Google Drive folders.
   - `SearchDriveSkill` (`search_drive`): Smart search by keyword across names, full text, and specific mime types.
3. **Registry & LLM Planner Integration**:
   - Registered in `app/registry/__init__.py`.
   - Added to `OpenCodeAdapter._KNOWN_TOOLS` in `app/modules/opencode/adapter.py` with parameter schema and updated system prompt.
4. **Frontend Presenter**:
   - `AI-Automation Frontend/app/components/ToolOutputViewer.js`: Added `DriveFilesView` rendering rich file cards with type icons, formatted size badges, direct Google Drive links (`webViewLink`), and ID copy buttons.
5. **Automated Verification**:
   - Unit tests in `tests/unit/test_drive_tools.py` covering mock mode, parameter validation, missing credentials handling, and file downloads.

---

*This log lives at `backend/IMPLEMENTATION_LOG.md` and should be updated after each module.*
