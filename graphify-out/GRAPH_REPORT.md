# Graph Report - Ai automation backend  (2026-09-15)

## Corpus Check
- 165 files · ~60,445 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 4, .example 1, .ico 1)

## Summary
- 1348 nodes · 2417 edges · 132 communities (85 shown, 28 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 139 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `73553adc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Jarvis Backend Implementation Log
- OpenCodeWorkerAgent
- resolve_path
- get_client
- registry/__init__.py
- WhatsAppClient
- pipelines.py
- server.js
- ScopedToolRegistry
- roadmap_phase_2.md
- test_memory.py
- OpenCodeAdapter
- TaskContract
- workers.py
- test_whatsapp.py
- WorkerSession
- Repository
- test_gmail_tools.py
- validate_path
- WorkerEngine
- agent.py
- What You Must Do When Invoked
- test_tools_and_routes.py
- test_agent_fork.py
- test_file_tools_v2.py
- EventBus
- ensure_exists
- main.py
- .__init__
- ListRecentEmailsPipeline
- LongTermMemory
- worker_agent.py
- _build_args
- [id]/page.js
- workers/page.js
- TestWorkersAPI
- poc.js
- frontend_routing/package.json
- delete_folder.py
- skills.py
- tools.py
- worker_events
- ToolRegistry
- Adding New Modules to the Jarvis Backend
- app/page.js
- Home
- test_frontend_integration.py
- test_search_content.py
- test_opencode_worker.py
- verify_content
- FakeAdapter
- gmail/helpers/validation.py
- FakeWhatsAppClient
- layout.js
- devDependencies
- scripts
- dependencies
- .execute
- whatsapp/helpers/validation.py
- _load_token_path
- agent/config.py
- setup_gmail_oauth.py
- compilerOptions
- next.config.mjs
- DailyDigestPipeline
- whatsapp/helpers/paths.py
- whatsapp/__init__.py
- Jarvis + OpenCode CLI Worker Architecture.md
- probe.js
- eslint.config.mjs
- postcss.config.mjs
- AGENTS.md — Jarvis AI Automation Backend
- 20. The Final Desired Experience
- 36. Development Order
- DownloadsNotifierPipeline
- jarvis-backend
- graphify reference: extra exports and benchmark
- PhotoBackupPipeline
- 11. Jarvis Should Generate the Worker Prompts
- 13. Worker Status
- ExecutionEngine
- client
- Read operations
- OrganizeDownloadsSkill
- graphify reference: query, path, explain
- engine
- .decide_next_step
- 16. Two Possible Automation Approaches
- 17. The Planned OpenCode Worker
- Module 1 – Backend Foundation & Core Config
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- events.py
- frontend_routing/README.md
- Quarterly Report
- Quarterly Report
- 7. Tool vs Skill vs Pipeline
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- Jarvis AI Backend Engine
- 3. OpenCode Has Two Different Ways of Being Used
- 32. Testing
- 33. Safety Requirements
- rules/graphify.md
- extraction-spec.md
- workflows/graphify.md
- frontend_routing/AGENTS.md
- Jarvis + OpenCode CLI Worker Architecture
- 8. Continuing the Same Session
- Phase 2 — Backend + File System Module
- 39. Instructions to the Implementing LLM
- 3. Technology Stack

## God Nodes (most connected - your core abstractions)
1. `BaseTool` - 81 edges
2. `RiskLevel` - 73 edges
3. `resolve_path()` - 61 edges
4. `validate_path()` - 47 edges
5. `ExecutionEngine` - 42 edges
6. `ensure_exists()` - 42 edges
7. `WorkerSession` - 38 edges
8. `WorkerEngine` - 35 edges
9. `get_client()` - 32 edges
10. `resolve_recipient()` - 28 edges

## Surprising Connections (you probably didn't know these)
- `test_adapter_accepts_bare_fork_step()` --uses--> `OpenCodeAdapter`  [INFERRED]
  backend/tests/unit/test_agent_fork.py → backend/app/modules/opencode/adapter.py
- `test_adapter_accepts_valid_plan_steps()` --uses--> `OpenCodeAdapter`  [INFERRED]
  backend/tests/unit/test_tools_and_routes.py → backend/app/modules/opencode/adapter.py
- `test_adapter_rejects_bad_plan_steps()` --uses--> `OpenCodeAdapter`  [INFERRED]
  backend/tests/unit/test_tools_and_routes.py → backend/app/modules/opencode/adapter.py
- `launch_worker()` --uses--> `TaskContract`  [INFERRED]
  backend/app/api/routes/workers.py → backend/app/workers/base/contract.py
- `_agent_factory_for()` --uses--> `TaskContract`  [INFERRED]
  backend/app/api/routes/workers.py → backend/app/workers/base/contract.py

## Import Cycles
- None detected.

## Communities (132 total, 28 thin omitted)

### Community 0 - "Jarvis Backend Implementation Log"
Cohesion: 0.05
Nodes (41): Addendum: attachments + agent robustness (same day), Agent can fork, Bug fixes along the way, ✅ Completed Modules, Context, Frontend, Jarvis Backend Implementation Log, Key Components Built (+33 more)

### Community 1 - "OpenCodeWorkerAgent"
Cohesion: 0.12
Nodes (16): factory(), OpenCodeWorkerAgent, The OpenCode worker's brain. Drives a milestone-based workflow: for each step…, Queue guidance from the parent (user / Jarvis) for the next milestone., asyncio, Mock run_opencode to simulate a successful milestone and verify the agent…, Verify the same session ID is passed to subsequent milestones., After all 4 milestones complete, decide_next_step returns done. (+8 more)

### Community 2 - "resolve_path"
Cohesion: 0.10
Nodes (18): Path, Resolve a user‑provided path string to an absolute Path. - Expands ``~`` to the…, resolve_path(), ensure_is_dir(), Any, Any, _file_hash(), Any (+10 more)

### Community 3 - "get_client"
Cohesion: 0.08
Nodes (21): get_client(), Return a value the sidecar can resolve: a full chat id, or a name/number string., resolve_recipient(), validate_group_action(), Any, Any, Any, DownloadMediaTool (+13 more)

### Community 4 - "registry/__init__.py"
Cohesion: 0.09
Nodes (32): ABC, BaseTool, Enum, str, Abstract base class for all filesystem tools. Subclasses must define ``name``,…, RiskLevel, AppendFileTool, Any (+24 more)

### Community 5 - "WhatsAppClient"
Cohesion: 0.09
Nodes (20): get_health(), HealthResponse, BaseModel, get, Settings, _get_creds(), _load_token_path(), Any (+12 more)

### Community 6 - "pipelines.py"
Cohesion: 0.12
Nodes (25): list_pipelines(), Any, get, post, Return a list of available pipeline names., Execute a pipeline by name with given parameters., run_pipeline(), ArchiveOldFilesPipeline (+17 more)

### Community 7 - "server.js"
Cohesion: 0.07
Nodes (28): dependencies, express, qrcode-terminal, venom-bot, description, main, name, scripts (+20 more)

### Community 8 - "ScopedToolRegistry"
Cohesion: 0.17
Nodes (7): Any, Return the tool instance if it is in the allowed set, else raise., Return only the allowed tools (name → tool instance)., Return the set of permitted tool names., A read‑only view of the global ``ToolRegistry`` that only exposes a whitelisted…, ScopedToolRegistry, TestScopedRegistry

### Community 9 - "roadmap_phase_2.md"
Cohesion: 0.06
Nodes (31): 10. Risk Levels, 11. Never Use Shell Commands for Normal File Operations, 12. Structured Tool Contract, 13. Verification, 14. Dry Run, 15. Idempotency, 16. Execution Engine, 17. Tool Registry (+23 more)

### Community 10 - "test_memory.py"
Cohesion: 0.09
Nodes (13): ChatMemory, Short-term chat memory: per-session sliding window of recent messages. Kept in-…, Stores the last ``max_messages`` messages per session., Return a copy of the session's message history (oldest first)., Clear one session, or all sessions when session_id is None., Agent memory: short-term chat memory and long-term persistent memory., fake_agent_env(), mem_db_factory() (+5 more)

### Community 11 - "OpenCodeAdapter"
Cohesion: 0.13
Nodes (14): OpenCodeAdapter, Any, Adapter to communicate with the Groq LLM and translate prompts into tool plans.…, Prompt used for single-step execution (legacy / fallback)., Send a chat-completion request from a full messages array and return content., Send a chat-completion request and return the raw content string., Parse the LLM's raw output as JSON, returning None on failure., Phase 1 — Analyze the user's prompt and return a plan or direct response. Args:… (+6 more)

### Community 12 - "TaskContract"
Cohesion: 0.13
Nodes (12): BaseModel, Ensure default allowed_tools is never None., Serialize to JSON for transport (parent ↔ worker session init)., Deserialize from JSON received from the parent., The task contract defines what a worker is expected to do, with strict…, TaskContract, _contract(), asyncio (+4 more)

### Community 13 - "workers.py"
Cohesion: 0.11
Nodes (26): _agent_factory_for(), cancel_worker(), _disk_sessions(), fork_worker(), ForkRequest, get_worker(), get_worker_artifact_file(), get_worker_result() (+18 more)

### Community 14 - "test_whatsapp.py"
Cohesion: 0.18
Nodes (19): asyncio, Tests for the WhatsApp module using a fake sidecar client., test_download_media_tool(), test_get_messages_tool(), test_list_chats_tool(), test_list_chats_unread_only(), test_manage_chat_tool(), test_manage_group_tool() (+11 more)

### Community 15 - "WorkerSession"
Cohesion: 0.11
Nodes (6): Path, Append a single JSON line to events.jsonl., Create the session directory and write the initial contract. Returns self for…, Manages a single worker's on-disk session state. On fork, creates the following…, WorkerSession, TestWorkerSession

### Community 16 - "Repository"
Cohesion: 0.11
Nodes (18): create_task(), get_task(), list_tasks(), Any, get, post, Session, update_task_status() (+10 more)

### Community 17 - "test_gmail_tools.py"
Cohesion: 0.33
Nodes (8): asyncio, fixture, setup_registry(), test_send_email_happy_path_no_creds(), test_send_email_missing_attachment_fails_fast(), test_send_email_missing_params(), test_send_email_mock_mode_with_attachment(), test_send_email_with_missing_creds_error()

### Community 18 - "validate_path"
Cohesion: 0.11
Nodes (16): Validate that a path is safe to operate on. Raises ``ValueError`` if the path…, validate_path(), Return a verification dict confirming existence of the path., verify_exists(), CopyTool, Any, CreateFileTool, Any (+8 more)

### Community 19 - "WorkerEngine"
Cohesion: 0.18
Nodes (9): Any, Queue a parent guidance message for the worker loop., Request cooperative cancellation of the worker loop., Fork the session and start the worker loop as a background task., Orchestrates a single worker session. Lifecycle: fork (create on‑disk session)…, Run one tool step: update state, emit events, record outcome. Returns (ok,…, Pass queued parent messages to the agent (and/or the event log)., Create the on‑disk worker session from a contract. (+1 more)

### Community 20 - "agent.py"
Cohesion: 0.15
Nodes (19): clear_history(), clear_memory(), _get_adapter(), get_history(), get_memory(), _learn_from_turn(), PromptRequest, Any (+11 more)

### Community 21 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 22 - "test_tools_and_routes.py"
Cohesion: 0.17
Nodes (15): test_unknown_worker_still_404s(), engine(), asyncio, fixture, Regression tests for tool fixes and API routes., test_adapter_accepts_valid_plan_steps(), test_adapter_rejects_bad_plan_steps(), test_agent_validation_errors() (+7 more)

### Community 23 - "test_agent_fork.py"
Cohesion: 0.21
Nodes (15): _execute_plan(), _fork_task(), Execute plan steps sequentially and return collected results., Fork a background worker session via the workers module. `fork` is a pseudo-…, get_engine(), Used by the agent route to look up engines after delegation., isolated_sessions(), asyncio (+7 more)

### Community 24 - "test_file_tools_v2.py"
Cohesion: 0.21
Nodes (16): engine(), asyncio, fixture, test_append_file_creates_and_appends(), test_archive_folder_and_extract_roundtrip(), test_bulk_rename_dry_run(), test_bulk_rename_extension_filter_and_start_index(), test_bulk_rename_with_counter() (+8 more)

### Community 25 - "EventBus"
Cohesion: 0.20
Nodes (5): emit(), EventBus, Send an event to all registered callbacks for *session_id*. Callbacks may be…, Helper that gives the worker engine a clean ``await bus.xxx`` API., TestEventBus

### Community 26 - "ensure_exists"
Cohesion: 0.15
Nodes (13): ensure_exists(), ensure_is_file(), is_protected(), Path, Return True if the path is within a protected location., DeleteFileTool, Any, ExtractTool (+5 more)

### Community 27 - "main.py"
Cohesion: 0.17
Nodes (16): ExecutionError, jarvis_exception_handler(), JarvisException, NotFoundError, Request, ValidationError, Any, lifespan() (+8 more)

### Community 29 - "ListRecentEmailsPipeline"
Cohesion: 0.22
Nodes (7): ListRecentEmailsPipeline, Any, Pipeline that runs the ListRecentEmailsSkill. Demonstrates how higher‑level…, asyncio, fixture, setup_skill(), test_list_recent_emails_pipeline_no_creds()

### Community 30 - "LongTermMemory"
Cohesion: 0.18
Nodes (7): LongTermMemory, SQLite-backed store of durable facts (deduplicated, capped)., Return up to ``limit`` most recent facts (oldest first)., Case-insensitive substring search over stored facts., Remove all facts. Returns how many were deleted., test_long_term_add_dedupe_and_list(), test_long_term_search_and_clear()

### Community 31 - "worker_agent.py"
Cohesion: 0.20
Nodes (11): setup_logging(), Any, Non-interactive OpenCode CLI client. Wraps ``opencode run`` as an async…, Result of a single ``opencode run`` invocation., Execute ``opencode run`` and collect structured results. Parameters ----------…, Execute opencode in a thread worker (optionally in a visible Windows terminal…, run_opencode(), _run_subprocess_sync() (+3 more)

### Community 32 - "_build_args"
Cohesion: 0.25
Nodes (5): _build_args(), _extract_session_id(), Try to extract the OpenCode session ID from events or raw output., Build the ``opencode run`` argument list., TestCLIClient

### Community 33 - "[id]/page.js"
Cohesion: 0.20
Nodes (5): ArtifactsPanel(), EVENT_STYLE, formatBytes(), STATUS_STYLE, WorkerPage()

### Community 34 - "workers/page.js"
Cohesion: 0.17
Nodes (6): DEFAULT_TOOLS, ForkForm(), STATUS_STYLE, TOOL_OPTIONS, WorkersPage(), react

### Community 36 - "poc.js"
Cohesion: 0.29
Nodes (9): clickSend(), isLoggedIn(), launchBrowser(), main(), path, PHONE, puppeteer, QR_SHOT (+1 more)

### Community 37 - "frontend_routing/package.json"
Cohesion: 0.20
Nodes (9): name, private, version, eslint, eslint-config-next, next, react-dom, tailwindcss (+1 more)

### Community 38 - "delete_folder.py"
Cohesion: 0.22
Nodes (6): move_to_trash(), Path, Recoverable-delete support: moves items into a backend-local trash folder., Move a file or folder into the trash directory and return its new path. The…, DeleteFolderTool, Any

### Community 39 - "skills.py"
Cohesion: 0.29
Nodes (7): list_skills(), Any, get, post, Return a list of registered skills (category == "skill")., Execute a skill by name with given parameters., run_skill()

### Community 40 - "tools.py"
Cohesion: 0.29
Nodes (7): list_tools(), Any, get, post, Return a list of registered tool names and descriptions., Execute a tool by name with given parameters., run_tool()

### Community 41 - "worker_events"
Cohesion: 0.29
Nodes (7): Request, SSE stream of this worker's events (live activity feed with disk replay…, worker_events(), _callback(), event_generator(), on(), Register a callback that will be invoked whenever the session emits an event.

### Community 42 - "ToolRegistry"
Cohesion: 0.15
Nodes (4): AgentFactory, # NOTE: params must match each tool's ``input_schema`` exactly — the plan, Registry that holds tool classes keyed by their name. Usage: registry =…, ToolRegistry

### Community 43 - "Adding New Modules to the Jarvis Backend"
Cohesion: 0.09
Nodes (22): 1. Module skeleton, 2. Register the new components, 2b. Make the tool available to the AGENT (essential!), 3.1 Tools endpoint, 3.2 Pipelines endpoint, 3. Expose the module via the API, 4. Optional: Add helper imports, 5. Quick checklist (+14 more)

### Community 44 - "app/page.js"
Cohesion: 0.32
Nodes (3): BotMessage(), UserBubble(), SUGGESTIONS

### Community 45 - "Home"
Cohesion: 0.31
Nodes (6): generateId(), Home(), callAgent(), confirmPlan(), sendPrompt(), loadStoredMessages()

### Community 47 - "test_search_content.py"
Cohesion: 0.38
Nodes (6): engine(), asyncio, fixture, test_search_content_case_sensitive_and_non_recursive(), test_search_content_finds_matches(), test_search_content_single_file_and_max_results()

### Community 48 - "test_opencode_worker.py"
Cohesion: 0.16
Nodes (13): build_prompt(), Milestone, MilestonePhase, plan_milestones(), Enum, str, Milestone Planner & Prompt Builder for Jarvis → OpenCode orchestration. Jarvis…, Build the full prompt string sent to ``opencode run``. Parameters ----------… (+5 more)

### Community 49 - "verify_content"
Cohesion: 0.60
Nodes (5): Any, Path, verify_content(), verify_is_dir(), verify_is_file()

### Community 51 - "gmail/helpers/validation.py"
Cohesion: 0.40
Nodes (4): Validate that a search query string is non‑empty., Basic validation for an email address string. Returns True if the string looks…, validate_email_address(), validate_query()

### Community 53 - "layout.js"
Cohesion: 0.40
Nodes (3): geistMono, geistSans, metadata

### Community 54 - "devDependencies"
Cohesion: 0.40
Nodes (5): devDependencies, eslint, eslint-config-next, tailwindcss, @tailwindcss/postcss

### Community 55 - "scripts"
Cohesion: 0.40
Nodes (5): scripts, build, dev, lint, start

### Community 56 - "dependencies"
Cohesion: 0.50
Nodes (4): dependencies, next, react, react-dom

### Community 58 - "whatsapp/helpers/validation.py"
Cohesion: 0.18
Nodes (10): normalize_phone(), Validation helpers for WhatsApp tools., Normalize a phone number to bare digits (no +, spaces, or dashes)., Convert a phone number or bare number to a WhatsApp chat id ('<digits>@c.us')., to_chat_id(), validate_chat_action(), Any, test_normalize_phone() (+2 more)

### Community 59 - "_load_token_path"
Cohesion: 0.25
Nodes (7): _get_creds(), _load_token_path(), Any, Credentials, Path, Load Gmail API credentials from token file or return None. Looks for…, Return credentials if present, otherwise respect ``GMAIL_MOCK``.

### Community 60 - "agent/config.py"
Cohesion: 0.12
Nodes (14): get_auto_approve(), get_milestone_timeout(), get_opencode_binary(), get_opencode_model(), get_opencode_server_url(), get_visible_console(), Configuration for the OpenCode CLI Worker. Resolves the ``opencode`` binary…, Return the path to the ``opencode`` CLI binary, or None if not found. (+6 more)

### Community 64 - "DailyDigestPipeline"
Cohesion: 0.33
Nodes (4): DailyDigestPipeline, Any, Run the unread digest and send it to the given chat (run on a schedule or on…, test_daily_digest_pipeline()

### Community 67 - "Jarvis + OpenCode CLI Worker Architecture.md"
Cohesion: 0.11
Nodes (18): 10. Why Milestones Are Better Than One Huge Prompt, 12. Jarvis Is the Supervisor, 14. OpenCode JSON Output, 15. Headless OpenCode Server, 18. Future Worker Architecture, 19. Why OpenCode Is a Good First Worker, 21. Core Principle, 22. First Implementation Goal (+10 more)

### Community 84 - "AGENTS.md — Jarvis AI Automation Backend"
Cohesion: 0.13
Nodes (14): Agent note (important), AGENTS.md — Jarvis AI Automation Backend, Architecture, Backend Conventions, DOM driver internals (`server.js`) — current WhatsApp Web realities, Gmail Module, Gotchas, Known limitations & optimization plan (next session) (+6 more)

### Community 85 - "20. The Final Desired Experience"
Cohesion: 0.15
Nodes (13): 20. The Final Desired Experience, Phase 10 — Correction, Phase 11 — Final Verification, Phase 12 — Final Report, Phase 1 — Planning, Phase 2 — Worker Assignment, Phase 3 — Session Creation, Phase 4 — Milestone 1 (+5 more)

### Community 86 - "36. Development Order"
Cohesion: 0.15
Nodes (13): 36. Development Order, Step 10 — Pipelines, Step 11 — API exposure, Step 12 — End-to-end test, Step 1 — Backend foundation, Step 2 — Core architecture, Step 3 — Tool system, Step 4 — File System helpers (+5 more)

### Community 87 - "DownloadsNotifierPipeline"
Cohesion: 0.67
Nodes (3): DownloadsNotifierPipeline, Notify a WhatsApp chat about files that appeared in a folder recently (e.g.…, test_downloads_notifier_pipeline()

### Community 91 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 92 - "PhotoBackupPipeline"
Cohesion: 0.67
Nodes (3): PhotoBackupPipeline, Download photos from a WhatsApp chat and store them in YYYY/MM folders., test_photo_backup_pipeline()

### Community 93 - "11. Jarvis Should Generate the Worker Prompts"
Cohesion: 0.22
Nodes (9): 11. Jarvis Should Generate the Worker Prompts, Constraints, Current Milestone, Expected Behavior, Overall Task, Project Context, Reporting Requirements, Requirements (+1 more)

### Community 94 - "13. Worker Status"
Cohesion: 0.22
Nodes (9): 13. Worker Status, Assigned, Blocked, Completed, Failed, Planning, Running, Verification (+1 more)

### Community 95 - "ExecutionEngine"
Cohesion: 0.16
Nodes (14): ExecutionEngine, Core engine that validates input, executes a tool, and returns a ToolResult.…, BaseModel, Standardized result returned by any tool execution., ToolResult, OrganizeDownloadsPipeline, Any, Pipeline that runs the OrganizeDownloadsSkill. It demonstrates how higher‑level… (+6 more)

### Community 97 - "Read operations"
Cohesion: 0.25
Nodes (8): 8. File System Tools, `exists`, `list_directory`, `metadata`, Mutation operations, `read_file`, Read operations, `search_files`

### Community 98 - "OrganizeDownloadsSkill"
Cohesion: 0.33
Nodes (4): OrganizeDownloadsSkill, Any, Path, Organize files in a download directory into subfolders by file extension.…

### Community 99 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 100 - "engine"
Cohesion: 0.67
Nodes (3): engine(), fake_client(), fixture

### Community 101 - ".decide_next_step"
Cohesion: 0.40
Nodes (3): Any, Append a compact result the next decision will see., Return the next action for the engine loop. Returns one of: - ``{"action":…

### Community 102 - "16. Two Possible Automation Approaches"
Cohesion: 0.40
Nodes (5): 16. Two Possible Automation Approaches, Advantages, Advantages, Approach A — Direct Non-Interactive Runs, Approach B — Persistent Headless OpenCode Server

### Community 103 - "17. The Planned OpenCode Worker"
Cohesion: 0.40
Nodes (5): 17. The Planned OpenCode Worker, Jarvis Responsibilities, Main Capabilities, Worker Identity, Worker Type

### Community 104 - "Module 1 – Backend Foundation & Core Config"
Cohesion: 0.40
Nodes (4): Files Created, Key Decisions, Module 1 – Backend Foundation & Core Config, Next Steps

### Community 105 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 106 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 107 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 108 - "events.py"
Cohesion: 0.67
Nodes (3): event_generator(), get, stream_events()

### Community 109 - "frontend_routing/README.md"
Cohesion: 0.50
Nodes (3): Deploy on Vercel, Getting Started, Learn More

### Community 110 - "Quarterly Report"
Cohesion: 0.50
Nodes (3): Outlook, Quarterly Report, Sales Figures

### Community 111 - "Quarterly Report"
Cohesion: 0.50
Nodes (3): Outlook, Quarterly Report, Sales Figures

### Community 112 - "7. Tool vs Skill vs Pipeline"
Cohesion: 0.50
Nodes (4): 7. Tool vs Skill vs Pipeline, Pipeline, Skill, Tool

### Community 116 - "3. OpenCode Has Two Different Ways of Being Used"
Cohesion: 0.67
Nodes (3): 3. OpenCode Has Two Different Ways of Being Used, Interactive Mode, Non-Interactive Mode

### Community 117 - "32. Testing"
Cohesion: 0.67
Nodes (3): 32. Testing, Integration tests, Unit tests

### Community 118 - "33. Safety Requirements"
Cohesion: 0.67
Nodes (3): 33. Safety Requirements, Instead, Never

## Knowledge Gaps
- **283 isolated node(s):** `jarvis-backend`, `name`, `version`, `description`, `main` (+278 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 639 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ExecutionEngine` connect `ExecutionEngine` to `registry/__init__.py`, `engine`, `skills.py`, `tools.py`, `ToolRegistry`, `test_whatsapp.py`, `test_search_content.py`, `test_gmail_tools.py`, `WorkerEngine`, `agent.py`, `test_tools_and_routes.py`, `test_file_tools_v2.py`, `main.py`, `ListRecentEmailsPipeline`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `WorkerEngine` connect `WorkerEngine` to `OpenCodeWorkerAgent`, `ScopedToolRegistry`, `worker_events`, `ToolRegistry`, `TaskContract`, `workers.py`, `WorkerSession`, `test_opencode_worker.py`, `test_agent_fork.py`, `EventBus`, `ExecutionEngine`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `BaseTool` connect `registry/__init__.py` to `OrganizeDownloadsSkill`, `resolve_path`, `get_client`, `delete_folder.py`, `ToolRegistry`, `validate_path`, `.execute`, `ensure_exists`, `ExecutionEngine`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `BaseTool` (e.g. with `ExecutionEngine` and `ToolRegistry`) actually correct?**
  _`BaseTool` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `RiskLevel` (e.g. with `OrganizeDownloadsSkill` and `AppendFileTool`) actually correct?**
  _`RiskLevel` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `ExecutionEngine` (e.g. with `ExecutionError` and `ValidationError`) actually correct?**
  _`ExecutionEngine` has 20 INFERRED edges - model-reasoned connections that need verification._
- **What connects `jarvis-backend`, `name`, `version` to the rest of the system?**
  _283 weakly-connected nodes found - possible documentation gaps or missing edges._