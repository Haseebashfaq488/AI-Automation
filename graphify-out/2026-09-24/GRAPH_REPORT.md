# Graph Report - AI-Automation  (2026-09-24)

## Corpus Check
- 221 files · ~96,428 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 5, .bat 5, .ico 1)

## Summary
- 1933 nodes · 3618 edges · 159 communities (116 shown, 26 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 263 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5f84b8df`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_opencode_worker.py
- test_whatsapp.py
- get_drive_service
- workers.py
- get_client
- registry/__init__.py
- server.js
- EventType
- WhatsAppClient
- roadmap_phase_2.md
- pipelines.py
- OrganizeDownloadsSkill
- test_gmail_tools.py
- ScopedToolRegistry
- antigravity_worker/agent/cli_client.py
- GlobalEventBus
- manage_chat.py
- What You Must Do When Invoked
- WorkerEngine
- AGENTS.md — Jarvis AI Automation Backend
- AI-Automation Frontend/package.json
- .analyze_prompt
- query
- test_memory.py
- resolve_path
- TaskContract
- test_agent_fork.py
- Repository
- OpenCodeAdapter
- WorkerSession
- ChatMemory
- Jarvis + OpenCode CLI Worker Architecture.md
- ToolOutputViewer.js
- agent.py
- AntigravityWorkerAgent
- Adding New Modules to the Jarvis Backend
- test_file_tools_v2.py
- opencode_worker/agent/milestones.py
- IMPLEMENTATION_LOG.md
- /graphify skill
- [id]/page.js
- Session: Gmail Tools, OAuth & Agent Email Routing (2026-09-12)
- JarvisEvent
- ValidationError
- PersistentAgyDaemon
- EventBus
- _contract
- test_tools_and_routes.py
- 📦 Jarvis Direct Tool Catalog
- ToolRegistry
- get
- models.py
- ListRecentEmailsPipeline
- WhatsAppInboundListener
- antigravity_worker/agent/milestones.py
- .inspect_event
- 20. The Final Desired Experience
- 36. Development Order
- apiFetch
- ExecutionEngine
- Jarvis Backend Implementation Log
- start_service.py
- publish_manual_event
- base/bus.py
- TestWorkersAPI
- app/page.js
- ExecutionEngine
- execution_engine.py
- GmailInboundListener
- ._load_session_from_db
- poc.js
- graphify reference: extra exports and benchmark
- Home
- 📁 Module Structure
- Milestone Decomposition
- report_63292881.md
- 11. Jarvis Should Generate the Worker Prompts
- 13. Worker Status
- verify_exists
- skills.py
- tools.py
- get_event_bus
- system.py
- run_tunnel.py
- Read operations
- VoiceInput.js
- JarvisBrainManager
- 🧠 JARVIS LIVING MEMORY & SYSTEM CONTEXT
- test_search_content.py
- graphify reference: query, path, explain
- Session: Worker / Orchestrator Architecture — Steps 0–1 (2026-09-12)
- Session: Optimizing the WhatsApp DOM Feature (2026-09-11)
- TestAntigravityConfig
- layout.js
- 1. Module skeleton
- clear_all_workers
- gmail/helpers/validation.py
- patch
- FakeAdapter
- Worker Session
- 16. Two Possible Automation Approaches
- 17. The Planned OpenCode Worker
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- setup_drive_oauth.py
- Jarvis AI Automation — Frontend Architecture & Agent Guide
- .execute
- graphify.js
- 7. Tool vs Skill vs Pipeline
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- _load_token_path
- compilerOptions
- next.config.mjs
- setup_gmail_oauth.py
- lifecycle.py
- Jarvis + OpenCode CLI Worker Architecture
- 3. OpenCode Has Two Different Ways of Being Used
- opencode.json
- 32. Testing
- 33. Safety Requirements
- Centralized Path Safety Layer
- rules/graphify.md
- extraction-spec.md
- workflows/graphify.md
- AI-Automation Frontend/AGENTS.md
- eslint.config.mjs
- postcss.config.mjs
- whatsapp/helpers/paths.py
- whatsapp/__init__.py
- antigravity_worker/__init__.py
- probe.js
- Phase 2 — Backend + File System Module
- 39. Instructions to the Implementing LLM
- 3. Technology Stack
- main.py
- write_file.py
- worker_events
- .__init__
- Worker Statuses
- jarvis-backend

## God Nodes (most connected - your core abstractions)
1. `BaseTool` - 97 edges
2. `RiskLevel` - 89 edges
3. `resolve_path()` - 61 edges
4. `ExecutionEngine` - 53 edges
5. `validate_path()` - 47 edges
6. `WorkerSession` - 43 edges
7. `ensure_exists()` - 42 edges
8. `WorkerEngine` - 40 edges
9. `TaskContract` - 38 edges
10. `JarvisEvent` - 37 edges

## Surprising Connections (you probably didn't know these)
- `Core Principle: Jarvis owns the task, OpenCode owns the implementation` --semantically_similar_to--> `LLM decides WHAT, backend decides HOW`  [INFERRED] [semantically similar]
  Jarvis + OpenCode CLI Worker Architecture.md → phases/roadmap_phase_2.md
- `test_adapter_accepts_bare_fork_step()` --uses--> `OpenCodeAdapter`  [INFERRED]
  backend/tests/unit/test_agent_fork.py → backend/app/modules/opencode/adapter.py
- `test_adapter_accepts_valid_plan_steps()` --uses--> `OpenCodeAdapter`  [INFERRED]
  backend/tests/unit/test_tools_and_routes.py → backend/app/modules/opencode/adapter.py
- `test_adapter_rejects_bad_plan_steps()` --uses--> `OpenCodeAdapter`  [INFERRED]
  backend/tests/unit/test_tools_and_routes.py → backend/app/modules/opencode/adapter.py
- `Agent Operating System (Jarvis as orchestration layer)` --conceptually_related_to--> `Jarvis AI Automation Backend`  [INFERRED]
  DESIGN_AND_PLAN_FOR_THE_NEXT_BIGGER_MODULE.md → AGENTS.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **graphify skill reference suite** — _agents_skills_graphify_skill_graphify, _agents_skills_graphify_references_extraction_spec, _agents_skills_graphify_references_github_and_merge, _agents_skills_graphify_references_update, _agents_skills_graphify_references_query, _agents_skills_graphify_references_transcribe, _agents_skills_graphify_references_add_watch, _agents_skills_graphify_references_exports, _agents_skills_graphify_references_hooks [EXTRACTED 1.00]
- **Jarvis system architecture** — agents_jarvis_ai_automation_backend, agents_whatsapp_sidecar, agents_gmail_module, agents_groq_planning_adapter [EXTRACTED 1.00]
- **Worker Session orchestration model** — design_and_plan_for_the_next_bigger_module_worker_session, design_and_plan_for_the_next_bigger_module_task_contract, design_and_plan_for_the_next_bigger_module_worker_state, design_and_plan_for_the_next_bigger_module_worker_permissions, design_and_plan_for_the_next_bigger_module_event_based_monitoring, design_and_plan_for_the_next_bigger_module_parent_worker_architecture [EXTRACTED 1.00]
- **File System Safety Model** — phases_roadmap_phase_2_path_safety, phases_roadmap_phase_2_protected_paths, phases_roadmap_phase_2_risk_levels, phases_roadmap_phase_2_dry_run, phases_roadmap_phase_2_verification [INFERRED 0.80]
- **Jarvis Manager / OpenCode Worker Orchestration** — jarvis___opencode_cli_worker_architecture_jarvis_supervisor, jarvis___opencode_cli_worker_architecture_opencode_sessions, jarvis___opencode_cli_worker_architecture_milestone_decomposition, backend_implementation_log_opencode_worker_session [INFERRED 0.85]
- **Tool/Skill/Pipeline Module Architecture** — backend_adding_modules_basetool, backend_adding_modules_toolregistry, backend_adding_modules_executionengine, phases_roadmap_phase_2_tool_skill_pipeline_distinction [INFERRED 0.85]

## Communities (159 total, 26 thin omitted)

### Community 0 - "test_opencode_worker.py"
Cohesion: 0.06
Nodes (43): _agent_factory_for(), factory(), Return an agent factory for the worker type, or None (placeholder loop)., _build_args(), _extract_session_id(), Any, Non-interactive OpenCode CLI client. Wraps ``opencode run`` as an async…, Try to extract the OpenCode session ID from events or raw output. (+35 more)

### Community 1 - "test_whatsapp.py"
Cohesion: 0.05
Nodes (43): normalize_phone(), Normalize a phone number to bare digits (no +, spaces, or dashes)., Convert a phone number or bare number to a WhatsApp chat id ('<digits>@c.us')., to_chat_id(), DailyDigestPipeline, Any, Run the unread digest and send it to the given chat (run on a schedule or on…, DownloadsNotifierPipeline (+35 more)

### Community 2 - "get_drive_service"
Cohesion: 0.10
Nodes (26): format_file_size(), get_drive_creds(), get_drive_service(), get_token_path(), is_mock_mode(), Credentials, Path, Find drive_token.json or fallback token.json in project paths. (+18 more)

### Community 3 - "workers.py"
Cohesion: 0.15
Nodes (18): cancel_worker(), fork_worker(), ForkRequest, intervene_worker(), InterveneRequest, launch_worker(), open_agy_terminal(), open_desktop() (+10 more)

### Community 4 - "get_client"
Cohesion: 0.08
Nodes (20): get_client(), Validation helpers for WhatsApp tools., Return a value the sidecar can resolve: a full chat id, or a name/number string., resolve_recipient(), validate_group_action(), Any, Any, Any (+12 more)

### Community 5 - "registry/__init__.py"
Cohesion: 0.09
Nodes (32): ABC, BaseTool, Enum, str, Abstract base class for all filesystem tools. Subclasses must define ``name``,…, RiskLevel, AppendFileTool, Any (+24 more)

### Community 6 - "server.js"
Cohesion: 0.08
Nodes (29): dependencies, express, qrcode-terminal, venom-bot, description, main, name, scripts (+21 more)

### Community 7 - "EventType"
Cohesion: 0.19
Nodes (12): HookRegistrationRequest, ManualEventRequest, BaseModel, Register a reactive follow-up action to execute when target_session_id…, register_task_hook(), get_orchestrator(), EventType, Enum (+4 more)

### Community 8 - "WhatsAppClient"
Cohesion: 0.09
Nodes (18): _get_creds(), _load_token_path(), Any, Credentials, Path, Return a path to a ``token.json`` if one exists next to the tool or at the…, Any, Any (+10 more)

### Community 9 - "roadmap_phase_2.md"
Cohesion: 0.06
Nodes (31): 10. Risk Levels, 11. Never Use Shell Commands for Normal File Operations, 12. Structured Tool Contract, 13. Verification, 14. Dry Run, 15. Idempotency, 16. Execution Engine, 17. Tool Registry (+23 more)

### Community 10 - "pipelines.py"
Cohesion: 0.11
Nodes (27): list_pipelines(), Any, get, post, Return a list of available pipeline names., Execute a pipeline by name with given parameters., run_pipeline(), ArchiveOldFilesPipeline (+19 more)

### Community 11 - "OrganizeDownloadsSkill"
Cohesion: 0.33
Nodes (4): OrganizeDownloadsSkill, Any, Path, Organize files in a download directory into subfolders by file extension.…

### Community 12 - "test_gmail_tools.py"
Cohesion: 0.33
Nodes (8): asyncio, fixture, setup_registry(), test_send_email_happy_path_no_creds(), test_send_email_missing_attachment_fails_fast(), test_send_email_missing_params(), test_send_email_mock_mode_with_attachment(), test_send_email_with_missing_creds_error()

### Community 13 - "ScopedToolRegistry"
Cohesion: 0.17
Nodes (7): Any, Return the tool instance if it is in the allowed set, else raise., Return only the allowed tools (name → tool instance)., Return the set of permitted tool names., A read‑only view of the global ``ToolRegistry`` that only exposes a whitelisted…, ScopedToolRegistry, TestScopedRegistry

### Community 14 - "antigravity_worker/agent/cli_client.py"
Cohesion: 0.10
Nodes (24): _build_args(), _extract_session_id(), Any, Non-interactive Antigravity CLI client. Wraps `agy run` (or configured CLI) as…, Execute `agy` via stream-json stdin/stdout and collect structured results., Build the argument list for official Antigravity CLI (`agy.exe`)., Try to extract the Antigravity session/conversation ID from events or raw…, run_antigravity_cli() (+16 more)

### Community 15 - "GlobalEventBus"
Cohesion: 0.10
Nodes (15): AbstractEventLoop, GlobalEventBus, Queue, Central Async Event Spine for Jarvis. Supports: - Multi-subscriber SSE queue…, Explicitly set or update the main asyncio loop for cross-thread calls., Return a snapshot of recently published events in chronological order., Subscribe a new asyncio.Queue to receive live streaming events., Remove an asyncio.Queue from active SSE subscribers. (+7 more)

### Community 16 - "manage_chat.py"
Cohesion: 0.18
Nodes (6): Connection states of the WhatsApp sidecar and human-readable descriptions., validate_chat_action(), GetStatusTool, Any, ManageChatTool, Any

### Community 17 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 18 - "WorkerEngine"
Cohesion: 0.19
Nodes (9): Any, Queue a parent guidance message for the worker loop., Request cooperative cancellation of the worker loop., Fork the session and start the worker loop as a background task., Orchestrates a single worker session. Lifecycle: fork (create on‑disk session)…, Run one tool step: update state, emit events, record outcome., Pass queued parent messages to the agent (and/or the event log)., Return real-time supervision status from the stream guardian. (+1 more)

### Community 19 - "AGENTS.md — Jarvis AI Automation Backend"
Cohesion: 0.08
Nodes (23): Agent note (important), AGENTS.md — Jarvis AI Automation Backend, Architecture, Backend Conventions, DOM driver internals (`server.js`) — current WhatsApp Web realities, Gmail Module, Gotchas, Groq planning adapter (opencode) (+15 more)

### Community 20 - "AI-Automation Frontend/package.json"
Cohesion: 0.08
Nodes (23): dependencies, next, react, react-dom, devDependencies, eslint, eslint-config-next, tailwindcss (+15 more)

### Community 21 - ".analyze_prompt"
Cohesion: 0.11
Nodes (12): Any, Append an entry to the scratchpad section in JARVIS_MEMORY.md. Deduplicates…, Record activity timestamp to reset idle timer., Evaluate instant conversational intents (<5ms response time)., Build structured planning prompt with complete tool knowledge., Safely extract JSON object from raw response text., Return required parameters for a tool from registry or fallback., Validate that all plan steps correspond to valid known tools. (+4 more)

### Community 22 - "query"
Cohesion: 0.12
Nodes (16): _build_index(), get_index(), Any, query(), Semantic tool selector: FAISS index over tool example phrases. Loaded once at…, Encode all example phrases and build a flat FAISS inner-product (cosine) index., Return or lazily initialize the global FAISS index., Return (best_tool_name, confidence_score) for the given prompt. Returns (None,… (+8 more)

### Community 23 - "test_memory.py"
Cohesion: 0.10
Nodes (12): LongTermMemory, SQLite-backed store of durable facts (deduplicated, capped)., Return up to ``limit`` most recent facts (oldest first)., Case-insensitive substring search over stored facts., Remove all facts. Returns how many were deleted., fake_agent_env(), mem_db_factory(), fixture (+4 more)

### Community 24 - "resolve_path"
Cohesion: 0.07
Nodes (37): Path, Resolve a user-provided path string to an absolute Path. - Rejects empty…, resolve_path(), move_to_trash(), Path, Recoverable-delete support: moves items into a backend-local trash folder., Move a file or folder into the trash directory and return its new path. The…, ensure_exists() (+29 more)

### Community 25 - "TaskContract"
Cohesion: 0.16
Nodes (13): BaseModel, The task contract defines what a worker is expected to do, with strict…, Ensure default allowed_tools is never None., Serialize to JSON for transport (parent ↔ worker session init)., TaskContract, Create the on‑disk worker session from a contract., ActiveStreamGuardian, Active Stream Guardian for Worker Supervision. Monitors real-time worker… (+5 more)

### Community 26 - "test_agent_fork.py"
Cohesion: 0.21
Nodes (15): _execute_plan(), _fork_task(), Execute plan steps sequentially and return collected results., Fork a background worker session via the workers module and record a tracked…, get_engine(), Used by the agent route to look up engines after delegation., isolated_sessions(), asyncio (+7 more)

### Community 27 - "Repository"
Cohesion: 0.17
Nodes (12): create_task(), get_task(), list_tasks(), Any, get, post, Session, update_task_status() (+4 more)

### Community 28 - "OpenCodeAdapter"
Cohesion: 0.13
Nodes (14): OpenCodeAdapter, Any, Prompt that makes the LLM return a structured plan (or direct response)., Adapter to communicate with the Groq LLM and translate prompts into tool plans.…, Prompt used for single-step execution (legacy / fallback)., Send a chat-completion request from a full messages array and return content., Send a chat-completion request and return the raw content string., Parse the LLM's raw output as JSON, returning None on failure. (+6 more)

### Community 29 - "WorkerSession"
Cohesion: 0.13
Nodes (5): Path, Append a single JSON line to events.jsonl., Create the session directory and write the initial contract. Returns self for…, Manages a single worker's on-disk session state. On fork, creates the following…, WorkerSession

### Community 30 - "ChatMemory"
Cohesion: 0.11
Nodes (13): ChatMemory, Short-term chat memory: per-session sliding window of recent messages. Ultra-…, Stores the last ``max_messages`` messages per session in RAM with async SQLite…, Clear session messages in RAM instantly and enqueue DB deletion., Wait for pending background SQLite writes to complete (used on test/shutdown)., Stop background worker thread cleanly., Ensure the chat_messages table exists (auto-create via SQLAlchemy)., Start daemon thread for non-blocking write-behind SQLite operations. (+5 more)

### Community 31 - "Jarvis + OpenCode CLI Worker Architecture.md"
Cohesion: 0.10
Nodes (20): 10. Why Milestones Are Better Than One Huge Prompt, 12. Jarvis Is the Supervisor, 14. OpenCode JSON Output, 15. Headless OpenCode Server, 18. Future Worker Architecture, 19. Why OpenCode Is a Good First Worker, 21. Core Principle, 22. First Implementation Goal (+12 more)

### Community 32 - "ToolOutputViewer.js"
Cohesion: 0.12
Nodes (13): CopyButton(), DRIVE_LIST_TOOLS, DriveFilesView(), EMAIL_TOOLS, FILE_ACTION_TOOLS, FILE_CONTENT_TOOLS, FILE_LIST_TOOLS, FileContentView() (+5 more)

### Community 33 - "agent.py"
Cohesion: 0.16
Nodes (19): clear_history(), clear_memory(), _get_adapter(), get_history(), get_memory(), _learn_from_turn(), PromptRequest, Any (+11 more)

### Community 34 - "AntigravityWorkerAgent"
Cohesion: 0.15
Nodes (13): Result of a single `agy run` invocation., RunResult, AntigravityWorkerAgent, Any, Autonomous agent driver powered by Antigravity CLI (`agy`)., Create a real-time event forwarder for SSE consumers., Record step result into agent history., Queue parent/manager guidance for the next turn. (+5 more)

### Community 35 - "Adding New Modules to the Jarvis Backend"
Cohesion: 0.11
Nodes (17): 2. Register the new components, 2b. Make the tool available to the AGENT (essential!), 3.1 Tools endpoint, 3.2 Pipelines endpoint, 3. Expose the module via the API, 4. Optional: Add helper imports, 5. Quick checklist, 6. Conventions to keep in sync (+9 more)

### Community 36 - "test_file_tools_v2.py"
Cohesion: 0.21
Nodes (16): engine(), asyncio, fixture, test_append_file_creates_and_appends(), test_archive_folder_and_extract_roundtrip(), test_bulk_rename_dry_run(), test_bulk_rename_extension_filter_and_start_index(), test_bulk_rename_with_counter() (+8 more)

### Community 37 - "opencode_worker/agent/milestones.py"
Cohesion: 0.17
Nodes (15): build_prompt(), is_simple_task(), Milestone, MilestonePhase, plan_milestones(), plan_milestones_llm_async(), Enum, str (+7 more)

### Community 38 - "IMPLEMENTATION_LOG.md"
Cohesion: 0.14
Nodes (12): ✅ Completed Modules, Module 1 – Backend Foundation & Core Config, Module 2 – Core Tool System & Execution Engine, Session: Optimizing the WhatsApp DOM Feature, Session: Worker / Orchestrator Architecture Steps 0-1, Jarvis AI Backend Engine, Setup & Running, Backend Python Dependencies (requirements.txt) (+4 more)

### Community 39 - "/graphify skill"
Cohesion: 0.18
Nodes (15): graphify always-on agent rule, Add URL and watch folder reference, Extra exports and benchmark reference, Extraction subagent prompt spec, GitHub clone and cross-repo merge reference, Commit hook and CLAUDE.md integration reference, Query, path, explain reference, Video/audio transcription reference (+7 more)

### Community 40 - "[id]/page.js"
Cohesion: 0.15
Nodes (8): ToolOutputViewer(), ArtifactsPanel(), EVENT_STYLE, formatBytes(), formatEventsToTerminal(), STATUS_STYLE, WorkerPage(), poll()

### Community 41 - "Session: Gmail Tools, OAuth & Agent Email Routing (2026-09-12)"
Cohesion: 0.40
Nodes (5): Addendum: attachments + agent robustness (same day), Session: Gmail Tools, OAuth & Agent Email Routing (2026-09-12), State, Tested & fixed end-to-end (all ✅), Verified live via backend (:8000)

### Community 42 - "JarvisEvent"
Cohesion: 0.23
Nodes (9): Any, Reactive Event-Driven Task Orchestrator. Allows Jarvis to chain dependent tasks…, Register a follow-up action to execute as soon as target_session_id completes., Handle worker completion and trigger all registered hooks., TaskOrchestrator, JarvisEvent, BaseModel, Serialize event to a JSON string suitable for SSE data field. (+1 more)

### Community 43 - "ValidationError"
Cohesion: 0.29
Nodes (7): ExecutionError, JarvisException, NotFoundError, Any, ValidationError, Any, Exception

### Community 44 - "PersistentAgyDaemon"
Cohesion: 0.20
Nodes (9): PersistentAgyDaemon, Maintains a persistent, warm background Antigravity CLI process. Uses `agy…, Start or verify the persistent background daemon process., Send a turn over the persistent stdin/stdout pipe with fallback., Gracefully stop the persistent daemon., asyncio, test_persistent_daemon_ensure_running(), test_persistent_daemon_send_turn_success() (+1 more)

### Community 45 - "EventBus"
Cohesion: 0.21
Nodes (5): emit(), EventBus, Helper that gives the worker engine a clean ``await bus.xxx`` API., Send an event to all registered callbacks for *session_id*. Callbacks may be…, TestEventBus

### Community 46 - "_contract"
Cohesion: 0.18
Nodes (7): Deserialize from JSON received from the parent., _contract(), asyncio, The worker must not be able to call tools outside allowed_tools., TestTaskContract, TestWorkerEngine, TestWorkerSession

### Community 47 - "test_tools_and_routes.py"
Cohesion: 0.12
Nodes (19): client(), fixture, test_unknown_worker_still_404s(), client(), fixture, engine(), asyncio, fixture (+11 more)

### Community 48 - "📦 Jarvis Direct Tool Catalog"
Cohesion: 0.13
Nodes (14): 1. 💬 WhatsApp Module Tools & Skills, 2. ✉️ Gmail Module Tools & Skills, 3. 📂 Google Drive Module Tools & Skills, 4. ⚡ Autonomous Antigravity Worker Delegation (`fork`), Antigravity Native Worker Capabilities:, 🧭 Core Architecture: Executive Orchestrator, Direct Conversational Response:, Executive Principles: (+6 more)

### Community 49 - "ToolRegistry"
Cohesion: 0.15
Nodes (4): AgentFactory, # NOTE: params must match each tool's ``input_schema`` exactly — the plan, Registry that holds tool classes keyed by their name. Usage: registry =…, ToolRegistry

### Community 50 - "get"
Cohesion: 0.14
Nodes (15): _disk_sessions(), get_worker(), get_worker_artifact_file(), get_worker_resolution(), get_worker_result(), get_worker_supervisor_status(), list_worker_artifacts(), list_workers() (+7 more)

### Community 51 - "models.py"
Cohesion: 0.19
Nodes (7): ChatMessage, Memory, Long-term agent memory: durable facts about the user and their preferences., Persisted per-session chat history so conversations survive backend restarts., Long-term memory: durable facts persisted in SQLite. These survive restarts and…, Add a fact. Returns False if empty or already known., Base

### Community 52 - "ListRecentEmailsPipeline"
Cohesion: 0.22
Nodes (7): ListRecentEmailsPipeline, Any, Pipeline that runs the ListRecentEmailsSkill. Demonstrates how higher‑level…, asyncio, fixture, setup_skill(), test_list_recent_emails_pipeline_no_creds()

### Community 53 - "WhatsAppInboundListener"
Cohesion: 0.22
Nodes (6): Continuous background listener that monitors WhatsApp chats and emits digest…, WhatsAppInboundListener, asyncio, test_gmail_inbound_listener_emits_event(), test_whatsapp_inbound_listener_emits_event(), on_event()

### Community 54 - "antigravity_worker/agent/milestones.py"
Cohesion: 0.21
Nodes (12): build_prompt(), is_simple_task(), Milestone, MilestonePhase, plan_milestones(), Enum, str, Milestone planning and prompt generation for the Antigravity Autonomous Worker.… (+4 more)

### Community 55 - ".inspect_event"
Cohesion: 0.21
Nodes (8): json_dump_safe(), Any, Identify execution of unit testing and dataflow testing suites., Return guardian health and observation status., Safe serializer to string for inspection., Inspect a stream event and return an intervention message if deviation is…, Verify that file paths manipulated by the worker remain within fs_scope., Detect repeated consecutive failures on the same command/tool.

### Community 56 - "20. The Final Desired Experience"
Cohesion: 0.15
Nodes (13): 20. The Final Desired Experience, Phase 10 — Correction, Phase 11 — Final Verification, Phase 12 — Final Report, Phase 1 — Planning, Phase 2 — Worker Assignment, Phase 3 — Session Creation, Phase 4 — Milestone 1 (+5 more)

### Community 57 - "36. Development Order"
Cohesion: 0.15
Nodes (13): 36. Development Order, Step 10 — Pipelines, Step 11 — API exposure, Step 12 — End-to-end test, Step 1 — Backend foundation, Step 2 — Core architecture, Step 3 — Tool system, Step 4 — File System helpers (+5 more)

### Community 58 - "apiFetch"
Cohesion: 0.21
Nodes (13): PowerControls(), handleCancelShutdown(), handleLock(), handleShutdownConfirm(), TaskChainTracker(), checkWorkerStatus(), apiFetch(), ForkForm() (+5 more)

### Community 59 - "ExecutionEngine"
Cohesion: 0.20
Nodes (12): BaseTool Contract, ExecutionEngine, OpenCodeAdapter _KNOWN_TOOLS, Module Skeleton (skills/tools/pipelines/helpers), ToolRegistry, Session: Gmail Tools, OAuth & Agent Email Routing, Phase 2 Definition of Done, Dry Run Support (+4 more)

### Community 60 - "Jarvis Backend Implementation Log"
Cohesion: 0.17
Nodes (12): Agent can fork, Frontend, Jarvis Backend Implementation Log, Key Components Built, Session: Fork UX — agent `fork` tool, manual fork form, chat persistence (2026-09-12), Session: Jarvis + OpenCode CLI Worker Architecture & Word Worker Removal (2026-09-15), Summary, Verified end-to-end flows (+4 more)

### Community 61 - "start_service.py"
Cohesion: 0.25
Nodes (17): clean_stale_chrome_locks(), cleanup(), establish_tunnel(), is_backend_running(), is_tunnel_alive(), is_whatsapp_running(), kill_proc(), log() (+9 more)

### Community 62 - "publish_manual_event"
Cohesion: 0.18
Nodes (10): get_recent_events(), publish_manual_event(), Any, get, post, Request, Return recently buffered events for instant UI loading., Manually publish an event to the global event bus. (+2 more)

### Community 63 - "base/bus.py"
Cohesion: 0.25
Nodes (8): emit_to_queues(), Any, Queue, Subscribe a new asyncio.Queue to receive live streaming events for session_id., Unsubscribe and remove an asyncio.Queue from session_id's active subscribers., Forward a streaming event to all active async queues subscribed to session_id…, subscribe(), unsubscribe()

### Community 65 - "app/page.js"
Cohesion: 0.18
Nodes (9): ActivityFeed(), formatTimestamp(), BotMessage(), UserBubble(), API_URL, getHeaders(), SUGGESTIONS, STATUS_STYLE (+1 more)

### Community 66 - "ExecutionEngine"
Cohesion: 0.23
Nodes (13): ExecutionEngine, Core engine that validates input, executes a tool, and returns a ToolResult.…, OrganizeDownloadsPipeline, Any, Pipeline that runs the OrganizeDownloadsSkill. It demonstrates how higher‑level…, asyncio, test_list_drive_files_mock_mode(), test_list_drive_files_no_creds() (+5 more)

### Community 67 - "execution_engine.py"
Cohesion: 0.21
Nodes (9): BaseModel, Standardized result returned by any tool execution., ToolResult, asyncio, test_execution_engine_list_directory(), asyncio, Path, test_dry_run_create_folder() (+1 more)

### Community 68 - "GmailInboundListener"
Cohesion: 0.24
Nodes (5): GmailInboundListener, _load_creds(), Any, Synchronous fetch executed in worker thread., Continuous background listener that monitors Gmail for new unread messages and…

### Community 69 - "._load_session_from_db"
Cohesion: 0.20
Nodes (5): Load the most recent max_messages rows from DB into RAM cache., Append a message in RAM instantly and enqueue background SQLite persist., Return a fast in-memory copy of the session's message history (<0.02ms)., Return a SQLAlchemy session or None if DB is unavailable., Background worker thread draining persistence queue to SQLite in high-speed…

### Community 70 - "poc.js"
Cohesion: 0.29
Nodes (9): clickSend(), isLoggedIn(), launchBrowser(), main(), path, PHONE, puppeteer, QR_SHOT (+1 more)

### Community 71 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 72 - "Home"
Cohesion: 0.31
Nodes (8): generateId(), Home(), callAgent(), checkHealth(), confirmPlan(), openOpenCodeTerminal(), sendPrompt(), loadStoredMessages()

### Community 73 - "📁 Module Structure"
Cohesion: 0.22
Nodes (9): Module 10 – Agent Memory, Module 3 – File System Safety & Path Helpers, Module 4 – Read-Only File System Tools, Module 5 – Mutation Tools & Dry-Run Engine, Module 6 – Database, Task Manager & Execution Journal, Module 7 – OpenCode (Groq) Integration Adapter, Module 8 – File System Skills & Pipelines, Module 9 – API Layer, Event Streaming & End-to-End Validation (+1 more)

### Community 74 - "Milestone Decomposition"
Cohesion: 0.22
Nodes (9): Session: OpenCode CLI Worker Architecture & Word Worker Removal, Core Principle: Jarvis owns the task, OpenCode owns the implementation, Future Worker Architecture (Cline, Word, Excel), Headless OpenCode Server, Jarvis as Supervisor, OpenCode JSON Output, Milestone Decomposition, OpenCode Non-Interactive run Command (+1 more)

### Community 75 - "report_63292881.md"
Cohesion: 0.22
Nodes (6): Outlook, Quarterly Report, Sales Figures, Outlook, Quarterly Report, Sales Figures

### Community 76 - "11. Jarvis Should Generate the Worker Prompts"
Cohesion: 0.22
Nodes (9): 11. Jarvis Should Generate the Worker Prompts, Constraints, Current Milestone, Expected Behavior, Overall Task, Project Context, Reporting Requirements, Requirements (+1 more)

### Community 77 - "13. Worker Status"
Cohesion: 0.22
Nodes (9): 13. Worker Status, Assigned, Blocked, Completed, Failed, Planning, Running, Verification (+1 more)

### Community 78 - "verify_exists"
Cohesion: 0.11
Nodes (12): Return a verification dict confirming existence of the path., verify_exists(), CopyTool, Any, CreateFileTool, Any, CreateFolderTool, Any (+4 more)

### Community 79 - "skills.py"
Cohesion: 0.29
Nodes (7): list_skills(), Any, get, post, Return a list of registered skills (category == "skill")., Execute a skill by name with given parameters., run_skill()

### Community 80 - "tools.py"
Cohesion: 0.29
Nodes (7): list_tools(), Any, get, post, Return a list of registered tool names and descriptions., Execute a tool by name with given parameters., run_tool()

### Community 81 - "get_event_bus"
Cohesion: 0.28
Nodes (7): get_event_bus(), Attach listener to the global event bus., MockWhatsAppTool, asyncio, test_task_orchestrator_auto_discovers_workspace_file(), test_task_orchestrator_chains_worker_completion(), test_task_orchestrator_multi_worker_pipeline_chaining()

### Community 82 - "system.py"
Cohesion: 0.22
Nodes (12): cancel_shutdown(), lock_workstation(), BaseModel, post, System control endpoints: Remote shutdown, restart, abort, and power management., Lock the Windows workstation immediately., Initiate a system shutdown with a safe countdown timer., Initiate a system restart with a countdown timer. (+4 more)

### Community 83 - "run_tunnel.py"
Cohesion: 0.71
Nodes (6): log(), main(), trigger_vercel_redeploy(), update_vercel_env(), wait_for_backend(), wait_for_network()

### Community 84 - "Read operations"
Cohesion: 0.25
Nodes (8): 8. File System Tools, `exists`, `list_directory`, `metadata`, Mutation operations, `read_file`, Read operations, `search_files`

### Community 85 - "VoiceInput.js"
Cohesion: 0.38
Nodes (4): playAudioCue(), SUPPORTED_LANGUAGES, useSpeechRecognition(), VoiceInput()

### Community 86 - "JarvisBrainManager"
Cohesion: 0.14
Nodes (24): get_brain_manager(), JarvisBrainManager, Jarvis Central Brain Manager powered by Antigravity CLI (`agy.exe`). Features:…, Central orchestrator for Jarvis's persistent Antigravity Brain., Synthesize a complete Master Task Specification prompt for autonomous workers., Return the global JarvisBrainManager instance., Antigravity module for Jarvis core brain and memory., build_master_task_prompt() (+16 more)

### Community 87 - "🧠 JARVIS LIVING MEMORY & SYSTEM CONTEXT"
Cohesion: 0.29
Nodes (6): 📌 Active Knowledge & Notes, 📜 Core Operational Rules (Manager Persona), 🛠️ Integrated Capabilities & Active Tools, 🧠 JARVIS LIVING MEMORY & SYSTEM CONTEXT, 📝 Scratchpad & Temporary Notes, 👤 User Profile & Preferences

### Community 88 - "test_search_content.py"
Cohesion: 0.38
Nodes (6): engine(), asyncio, fixture, test_search_content_case_sensitive_and_non_recursive(), test_search_content_finds_matches(), test_search_content_single_file_and_max_results()

### Community 89 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 90 - "Session: Worker / Orchestrator Architecture — Steps 0–1 (2026-09-12)"
Cohesion: 0.33
Nodes (6): Bug fixes along the way, Not yet done (next sessions), Session: Worker / Orchestrator Architecture — Steps 0–1 (2026-09-12), Step 0 — plumbing (done earlier same day), Step 1 — Word worker + worker LLM (this session), Verification

### Community 91 - "Session: Optimizing the WhatsApp DOM Feature (2026-09-11)"
Cohesion: 0.33
Nodes (6): Context, Known limitations, Optimization plan (accepted next steps, not yet implemented), Root causes found & fixed (live debugging against real WhatsApp Web), Session: Optimizing the WhatsApp DOM Feature (2026-09-11), Verified live (through backend `:8000`, all ✅)

### Community 93 - "layout.js"
Cohesion: 0.40
Nodes (3): geistMono, geistSans, metadata

### Community 94 - "1. Module skeleton"
Cohesion: 0.40
Nodes (5): 1. Module skeleton, Helper example (`helpers/validation.py`), Minimal pipeline example (`pipelines/list_recent_emails_pipeline.py`), Minimal skill example (`skills/list_recent_emails.py`), Minimal tool example (`tools/send_email_tool.py`)

### Community 95 - "clear_all_workers"
Cohesion: 0.67
Nodes (3): clear_all_workers(), delete, Purge all on-disk worker sessions and clear the in-memory engine cache.

### Community 96 - "gmail/helpers/validation.py"
Cohesion: 0.40
Nodes (4): Validate that a search query string is non‑empty., Basic validation for an email address string. Returns True if the string looks…, validate_email_address(), validate_query()

### Community 97 - "patch"
Cohesion: 0.36
Nodes (8): asyncio, Unit tests for system power management endpoints., test_cancel_shutdown_endpoint(), test_cancel_shutdown_tool_execution(), test_restart_endpoint(), test_shutdown_endpoint(), test_shutdown_tool_execution(), patch

### Community 100 - "Worker Session"
Cohesion: 0.40
Nodes (5): Event-based parent monitoring, Worker Task Contract, Worker permissions model, Worker Session, Worker State

### Community 101 - "16. Two Possible Automation Approaches"
Cohesion: 0.40
Nodes (5): 16. Two Possible Automation Approaches, Advantages, Advantages, Approach A — Direct Non-Interactive Runs, Approach B — Persistent Headless OpenCode Server

### Community 102 - "17. The Planned OpenCode Worker"
Cohesion: 0.40
Nodes (5): 17. The Planned OpenCode Worker, Jarvis Responsibilities, Main Capabilities, Worker Identity, Worker Type

### Community 103 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 104 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 105 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 106 - "setup_drive_oauth.py"
Cohesion: 0.50
Nodes (4): get_available_credentials(), main(), Setup script to run the Google Drive OAuth flow and save drive_token.json. This…, Find all potential OAuth client credentials available in the project.

### Community 107 - "Jarvis AI Automation — Frontend Architecture & Agent Guide"
Cohesion: 0.12
Nodes (14): 1. Overview & Separation of Concerns, 2. Key Pages & Routes, 3. Core Components, 4. Environment Variables, 5. Deployment on Vercel, Jarvis AI Automation — Frontend Architecture & Agent Guide, 1. Install Dependencies, 2. Configure Environment (+6 more)

### Community 109 - "graphify.js"
Cohesion: 0.67
Nodes (3): graphAgeDays(), GraphifyPlugin(), IMPORTANT: keep the reminder string free of backticks and $(...) constructs.

### Community 110 - "7. Tool vs Skill vs Pipeline"
Cohesion: 0.50
Nodes (4): 7. Tool vs Skill vs Pipeline, Pipeline, Skill, Tool

### Community 113 - "_load_token_path"
Cohesion: 0.25
Nodes (7): _get_creds(), _load_token_path(), Any, Credentials, Path, Load Gmail API credentials from token file or return None. Looks for…, Return credentials if present, otherwise respect ``GMAIL_MOCK``.

### Community 117 - "lifecycle.py"
Cohesion: 0.48
Nodes (6): lifespan(), FastAPI, get_gmail_listener(), get_whatsapp_listener(), get_persistent_agy_daemon(), Return the global PersistentAgyDaemon instance.

### Community 118 - "Jarvis + OpenCode CLI Worker Architecture"
Cohesion: 0.67
Nodes (3): OpenCode CLI/Server Documentation, 1. Purpose, Jarvis + OpenCode CLI Worker Architecture

### Community 119 - "3. OpenCode Has Two Different Ways of Being Used"
Cohesion: 0.67
Nodes (3): 3. OpenCode Has Two Different Ways of Being Used, Interactive Mode, Non-Interactive Mode

### Community 121 - "32. Testing"
Cohesion: 0.67
Nodes (3): 32. Testing, Integration tests, Unit tests

### Community 122 - "33. Safety Requirements"
Cohesion: 0.67
Nodes (3): 33. Safety Requirements, Instead, Never

### Community 123 - "Centralized Path Safety Layer"
Cohesion: 0.67
Nodes (3): Centralized Path Safety Layer, Protected Paths, Tool Risk Levels

### Community 140 - "main.py"
Cohesion: 0.13
Nodes (16): get_health(), HealthResponse, BaseModel, get, Settings, jarvis_exception_handler(), Request, create_app() (+8 more)

### Community 141 - "write_file.py"
Cohesion: 0.31
Nodes (7): Any, Path, verify_content(), verify_is_dir(), verify_is_file(), Any, WriteFileTool

### Community 142 - "worker_events"
Cohesion: 0.20
Nodes (10): Request, SSE stream of this worker's events (live activity feed with disk replay…, Real-time SSE stream of raw Antigravity CLI events (step_update deltas, tool…, worker_events(), _callback(), event_generator(), worker_stream(), stream_generator() (+2 more)

## Knowledge Gaps
- **336 isolated node(s):** `$schema`, `plugin`, `FILE_LIST_TOOLS`, `FILE_CONTENT_TOOLS`, `FILE_ACTION_TOOLS` (+331 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 864 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ExecutionEngine` connect `ExecutionEngine` to `agent.py`, `test_whatsapp.py`, `execution_engine.py`, `test_file_tools_v2.py`, `registry/__init__.py`, `EventType`, `JarvisEvent`, `ValidationError`, `test_gmail_tools.py`, `skills.py`, `tools.py`, `ToolRegistry`, `WorkerEngine`, `test_tools_and_routes.py`, `ListRecentEmailsPipeline`, `test_search_content.py`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `ChatMemory` connect `ChatMemory` to `agent.py`, `models.py`, `._load_session_from_db`, `test_memory.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `OpenCodeAdapter` connect `OpenCodeAdapter` to `agent.py`, `test_agent_fork.py`, `test_tools_and_routes.py`, `ToolRegistry`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `BaseTool` (e.g. with `ExecutionEngine` and `ToolRegistry`) actually correct?**
  _`BaseTool` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 43 inferred relationships involving `RiskLevel` (e.g. with `SearchDriveSkill` and `ListDriveFilesTool`) actually correct?**
  _`RiskLevel` has 43 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `ExecutionEngine` (e.g. with `TaskOrchestrator` and `ExecutionError`) actually correct?**
  _`ExecutionEngine` has 28 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `plugin`, `FILE_LIST_TOOLS` to the rest of the system?**
  _336 weakly-connected nodes found - possible documentation gaps or missing edges._