# AGENTS.md — Jarvis AI Automation Backend

## Project Overview
Personal AI assistant ("Jarvis") with a FastAPI backend, Next.js frontend, and a
Node.js **WhatsApp sidecar** that automates WhatsApp Web via a custom Puppeteer
DOM driver (no whatsapp-web.js / venom — both abandoned and incompatible with
current WhatsApp Web builds).

## Architecture & Repositories

```
Frontend (Next.js 16)   :3000   AI-Automation Frontend/   (Repo: Haseebashfaq488/Ai-Automation-Frontend)
Backend  (FastAPI)      :8000   backend/                  (Repo: Haseebashfaq488/AI-Automation)
WhatsApp sidecar (Node) :4097   backend/whatsapp_service/server.js
        │
        ▼
Headless Chrome ──► live WhatsApp Web session (logged in via copied profile)
```

> **Note on Repositories**: 
> - Root repository (`Haseebashfaq488/AI-Automation`) houses the full workspace, FastAPI backend engine, Antigravity brain, and worker daemons.
> - Frontend repository (`Haseebashfaq488/Ai-Automation-Frontend`) is the standalone Next.js 16 web interface deployed to Vercel.

---

## Living Documentation System & Agent Navigation Rules

> [!IMPORTANT]
> **MANDATORY FIRST STEP BEFORE ANY BACKEND CODE CHANGE:**
> Before inspecting, modifying, or creating code in any backend folder, you **MUST** first read that directory's local `README.md`. 
> Do **NOT** crawl through hundreds of lines of code or guess contracts. Each folder maintains an authoritative living contract with file tables, API routes, and critical invariants.

### Backend Living Documentation Map:
| Directory | Local Living Doc | What It Explains |
| :--- | :--- | :--- |
| **`backend/`** | [`backend/README.md`](file:///d:/AI-Automation/backend/README.md) | High-level engine overview, environment variables, OAuth setup, and runbook. |
| **`backend/app/`** | [`backend/app/README.md`](file:///d:/AI-Automation/backend/app/README.md) | FastAPI app factory (`main.py`), CORS middleware, lifespan events, and lazy loading. |
| **`backend/app/api/`** | [`backend/app/api/README.md`](file:///d:/AI-Automation/backend/app/api/README.md) | Full route inventory (`/agent`, `/workers`, `/events`), request schemas, and SSE streams. |
| **`backend/app/core/`** | [`backend/app/core/README.md`](file:///d:/AI-Automation/backend/app/core/README.md) | Universal `BaseTool` contract, in-memory event bus, and reactive downstream orchestrator. |
| **`backend/app/modules/`**| [`backend/app/modules/README.md`](file:///d:/AI-Automation/backend/app/modules/README.md) | Domain plugins (Drive, Gmail, Database, Memory, Files) and OAuth token rules. |
| **`backend/app/workers/`**| [`backend/app/workers/README.md`](file:///d:/AI-Automation/backend/app/workers/README.md) | 3-job worker protocol, living docs scanner, and graphify handover synthesis. |
| **`backend/tests/`** | [`backend/tests/README.md`](file:///d:/AI-Automation/backend/tests/README.md) | Test suites list, pytest conventions, and external API mocking patterns. |

### How to Maintain & Update Folder Documentation:
1. **When Modifying Existing Code**:
   * If you add new tools, alter route parameters, or introduce new database models, update the file inventory and contracts in that folder's `README.md`.
2. **When Resolving Edge Cases / Bugs**:
   * Record the root cause and guardrail in the **Critical Invariants & Gotchas** section of that folder's `README.md`.
3. **When Creating a New Folder**:
   * Add a `README.md` following the **Standard Anatomy**:
     1. *Directory Role & Boundary*
     2. *File Inventory & Roles Table*
     3. *External Contracts & APIs*
     4. *Critical Invariants & Gotchas*
     5. *Extension Guide*
4. **Code Knowledge Graph**:
   * Always run `graphify update .` after modifying code files to keep the AST knowledge graph synchronized.

---

- Backend tools/skills/pipelines → `app/modules/whatsapp/helpers/client.py`
  (singleton `get_client()`, tests monkeypatch with `FakeWhatsAppClient`)
  → sidecar REST API.
- Backend contract with the sidecar is FIXED: `/status /qr /chats /messages
  /send /send-file /contacts /chat-info /chat/action /group /media`.
  Endpoints the DOM driver doesn't implement return **501** (deliberate stubs).

## Running Everything

```powershell
# 1. WhatsApp sidecar (from backend/whatsapp_service)
npm start                              # node server.js on :4097

# 2. Backend (from backend)
uvicorn app.main:app --port 8000       # or however it's normally started

# 3. Frontend (from AI-Automation Frontend)
npm run dev                            # :3000
```

Health checks: `GET :8000/health`, `GET :4097/status`, `GET :3000`.

## WhatsApp Module — Critical Details

### Session model
- Uses a **copy** of the user's Chrome profile: `backend/whatsapp_service/chrome_profile_copy/`
  (profile `Default`). Chrome v153 blocks `--remote-debugging-port` on the real
  user-data dir — that's why the copy is mandatory.
- **Refresh the copy**: run `sync_profile.ps1` (robocopy) **while Chrome is fully closed**.
- If the session dies: delete `chrome_profile_copy/`, re-run the sync, restart the sidecar.
- User's phone: **+923098956995** — use for all live send tests (message self).
- Run Python scripts with `$env:PYTHONIOENCODING = "utf-8"` (emoji printing crashes cp1252 console).

### DOM driver internals (`server.js`) — current WhatsApp Web realities
- Search box is a plain `<input class="html-input">` inside
  `[data-testid="chat-list-search-container"]`. Set its value via the native
  `HTMLInputElement.prototype.value` setter + `input` event — React drops focus
  on `keyboard.type` (keystrokes get lost).
- Search results are `[data-testid="cell-frame-container"]` (no `role="listitem"`).
  Click via element **handle** (JS `.click()` doesn't navigate); wait for `#main`.
- Phone-number chats (incl. the self-chat) are NOT searchable → route via
  `web.whatsapp.com/send?phone=<digits>` URL (`phoneDigits()` helper).
- **Document upload**: WA Web has NO document `<input>` in the DOM (only a
  permanent hidden `image/*` one; `showOpenFilePicker` unused; synthetic
  DragEvent drops are ignored). Working flow: click attach → click
  "Document"/"Photos & videos" menu item → `page.waitForFileChooser()` →
  `chooser.accept([path])`. WA creates the input dynamically and removes it
  when the dialog closes.
- Messages: bubbles are `[data-testid="msg-container"]` (old `div.message-in/out`
  gone). `fromMe` = positional (outgoing bubbles hug the right edge of `#main`,
  gap ≈57px vs ≥300px incoming; threshold 120px) — tick icons lost stable testids.
- Failure-path screenshots: `dbg_search_fail.png`, `dbg_chat_open_fail.png`,
  `dbg_send_fail.png` (in whatsapp_service/).

### Status of the 11 backend WhatsApp tools
- Working live: `whatsapp_status`, `list_chats`, `get_messages`, `send_message`, `send_file`.
- 501 stubs: `list_contacts`, `get_chat_info`, `manage_chat`, `manage_group`, `download_media`.
- Also: 2 skills (`send_report`, `unread_digest`), 3 pipelines (`daily_digest`,
  `downloads_notifier`, `photo_backup`) registered in the backend.

## Gmail Module
- `app/modules/gmail/`: `send_email` tool (supports **attachments**: optional
  `attachments` list of absolute file paths, ~25 MB cap), `list_recent_emails`
  skill (`query` optional, defaults to `in:inbox`), `list_recent_emails` pipeline.
- OAuth token lives at **`backend/token.json`** (scopes: `gmail.send` +
  `gmail.readonly`). Both the tool and the skill auto-refresh expired tokens
  and persist them back to the file. Never save tokens elsewhere — the tools
  only look module-local or at `backend/token.json`.
- Re-auth: `python setup_gmail_oauth.py` (from `backend/`) → browser flow →
  saves to `backend/token.json`.
- `GMAIL_MOCK=1` env var makes both tool/skill return fake data (used for demos).
- Gmail tests monkeypatch `_load_token_path → None`; they must stay independent
  of whether a real `token.json` exists.

## Google Drive Module
- `app/modules/drive/`:
  - Tools: `list_drive_files` (list & filter files with pagination/size/type), `read_drive_file` (read Google Docs/Sheets/plain-text or download files), `upload_drive_file` (upload local files to Drive folders).
  - Skill: `search_drive` (full-text and keyword search across Drive with `file_type` filters).
- OAuth token lives at **`backend/drive_token.json`** (scopes: `drive.readonly`, `drive.file`, `drive.metadata.readonly`). The client helper auto-refreshes tokens and falls back to `token.json` if unified.
- Re-auth: `python setup_drive_oauth.py` (fixed port `8080`, saves to `backend/drive_token.json`).
- `DRIVE_MOCK=1` env var makes all Drive tools/skills return structured mock data.

### Agent note (important)
- The Groq planning prompt in `app/modules/opencode/adapter.py` is
  **general-purpose** (files + WhatsApp + email). Do NOT narrow it back to
  "file-system assistant" — that was the root cause of the agent replying
  "I'm not sure what file operation you need" to email/WhatsApp requests.
- `_KNOWN_TOOLS` in the adapter must stay in sync with the registry: plan
  validation silently drops steps whose tool is unknown or whose required
  params are missing (that silent drop was the other half of the bug).

### Known limitations & optimization plan (next session)
- Speed: `send_message` ≈10–20 s, `send_file` ≈30–45 s, sidecar boot ≈30–45 s.
  Causes: per-message `page.goto()` full reloads, fixed `sleep()` padding,
  serialized request queue.
- Accepted plan (not yet implemented):
  1. Persistent Chrome (`--remote-debugging-port` + `puppeteer.connect()`) → instant restarts.
  2. Reuse the already-open chat instead of `page.goto` when the target is unchanged.
  3. Replace fixed sleeps with condition waits (`waitForSelector`/`waitForFunction`).
  4. Request-interception to block images/media.
  - Target: send ≈2–4 s, send_file ≈5–8 s.
- Alternatives considered and deferred: Baileys (WS protocol; needs fresh QR
  pairing + ban risk), official WhatsApp Business API (paid).

## Backend Conventions
- Tool contract: `BaseTool` (`app/core/tool.py`) with `RiskLevel` + `category`
  ("tool" | "skill" | "pipeline"); `ToolResult` for outputs.
- Modules live under `app/modules/<name>/{helpers,tools,skills,pipelines}/`.
- File-management module: 11 tools incl. dry-run support, protected-path
  refusal, delete-to-trash, archive/extract roundtrip.
- Agent: two-phase flow (`/agent/run` → plan, then `confirm=true` + `plan_id`),
  Groq LLM, chat memory (20-msg sliding window) + long-term SQLite memory.
- Tests: `pytest` (70 passing at last run); run from `backend/`.

## Logs & Docs
- **Maintained log**: `backend/IMPLEMENTATION_LOG.md` — update after each module/session.
  Latest session: *"Optimizing the WhatsApp DOM Feature"* (2026-09-11) — full root-cause
  analysis of the DOM driver fixes + the optimization plan.
- `implementation_log/IMPLEMENTATION_LOG.md` is an older Phase-2 historical copy.
- `frontend_routing/AGENTS.md` is auto-generated by `next dev` (Next.js rules) — don't edit.

## Gotchas
- Never run `sync_profile.ps1` while Chrome is open (locks/corrupts the copy).
- Killing the sidecar mid-request can leave the enqueue chain wedged — restart cleanly.
- whatsapp-web.js / venom-bot must NOT be reintroduced (abandoned, broken with
  current WA Web; `package.json` may still reference them but `server.js` only
  needs `puppeteer`).
