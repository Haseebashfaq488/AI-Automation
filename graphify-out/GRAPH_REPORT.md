# Graph Report - AI-Automation  (2026-09-24)

## Corpus Check
- 227 files · ~107,937 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 5, .bat 5, .ico 1)

## Summary
- 2061 nodes · 3907 edges · 165 communities (121 shown, 27 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 282 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e6eca5ab`
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
- ServiceMemoryManager
- test_gmail_tools.py
- ScopedToolRegistry
- AntigravityWorkerAgent
- JarvisEvent
- delete_file.py
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
- FakeWhatsAppClient
- Adding New Modules to the Jarvis Backend
- test_file_tools_v2.py
- opencode_worker/agent/milestones.py
- IMPLEMENTATION_LOG.md
- /graphify skill
- [id]/page.js
- ._ensure_dir
- TaskOrchestrator
- main.py
- PersistentAgyDaemon
- EventBus
- _contract
- test_tools_and_routes.py
- 📦 Jarvis Direct Tool Catalog
- send_file.py
- DriveInboundListener
- service_memory.py
- ListRecentEmailsSkill
- WhatsAppInboundListener
- antigravity_worker/agent/milestones.py
- core/config.py
- 20. The Final Desired Experience
- 36. Development Order
- apiFetch
- ExecutionEngine
- Jarvis Backend Implementation Log
- start_service.py
- events.py
- tasks.py
- TestWorkersAPI
- app/page.js
- ExecutionEngine
- execution_engine.py
- GmailInboundListener
- manage_chat.py
- poc.js
- graphify reference: extra exports and benchmark
- Home
- 📁 Module Structure
- Milestone Decomposition
- report_63292881.md
- 11. Jarvis Should Generate the Worker Prompts
- 13. Worker Status
- JarvisBrainManager
- skills.py
- tools.py
- get_service_memory_manager
- system.py
- run_tunnel.py
- Read operations
- VoiceInput.js
- test_antigravity_brain.py
- 🧠 JARVIS LIVING MEMORY & SYSTEM CONTEXT
- test_search_content.py
- graphify reference: query, path, explain
- Session: Worker / Orchestrator Architecture — Steps 0–1 (2026-09-12)
- Session: Optimizing the WhatsApp DOM Feature (2026-09-11)
- TestAntigravityConfig
- layout.js
- 1. Module skeleton
- Chat.js
- gmail/helpers/validation.py
- patch
- FakeAdapter
- test_mutation_tools.py
- Worker Session
- 16. Two Possible Automation Approaches
- 17. The Planned OpenCode Worker
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- setup_drive_oauth.py
- Jarvis AI Automation — Frontend Architecture & Agent Guide
- ToolRegistry
- graphify.js
- 7. Tool vs Skill vs Pipeline
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- _load_token_path
- compilerOptions
- next.config.mjs
- setup_gmail_oauth.py
- UnreadDigestSkill
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
- test_frontend_integration.py
- write_file.py
- base/bus.py
- normalize_phone
- Session: Gmail Tools, OAuth & Agent Email Routing (2026-09-12)
- Worker Statuses
- jarvis-backend
- SendReportSkill
- DownloadsNotifierPipeline
- PhotoBackupPipeline
- engine

## God Nodes (most connected - your core abstractions)
1. `BaseTool` - 103 edges
2. `RiskLevel` - 95 edges
3. `resolve_path()` - 61 edges
4. `ExecutionEngine` - 53 edges
5. `WorkerSession` - 49 edges
6. `validate_path()` - 47 edges
7. `Repository` - 42 edges
8. `ensure_exists()` - 42 edges
9. `WorkerEngine` - 42 edges
10. `get_client()` - 41 edges

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

## Communities (165 total, 27 thin omitted)

### Community 0 - "test_opencode_worker.py"
Cohesion: 0.06
Nodes (40): _build_args(), _extract_session_id(), Any, Non-interactive OpenCode CLI client. Wraps ``opencode run`` as an async…, Try to extract the OpenCode session ID from events or raw output., Result of a single ``opencode run`` invocation., Execute ``opencode run`` and collect structured results. Parameters ----------…, Build the ``opencode run`` argument list. (+32 more)

### Community 1 - "test_whatsapp.py"
Cohesion: 0.17
Nodes (20): asyncio, Tests for the WhatsApp module using a fake sidecar client., test_download_media_tool(), test_get_messages_tool(), test_get_recent_whatsapp_activity_tool(), test_get_unread_messages_tool(), test_get_whatsapp_chat_messages_tool(), test_list_chats_tool() (+12 more)

### Community 2 - "get_drive_service"
Cohesion: 0.09
Nodes (28): format_file_size(), get_drive_creds(), get_drive_service(), get_token_path(), is_mock_mode(), Credentials, Path, Find drive_token.json or fallback token.json in project paths. (+20 more)

### Community 3 - "workers.py"
Cohesion: 0.06
Nodes (51): _agent_factory_for(), factory(), approve_worker_plan(), ApprovePlanRequest, cancel_worker(), clear_all_workers(), _disk_sessions(), fork_worker() (+43 more)

### Community 4 - "get_client"
Cohesion: 0.07
Nodes (25): get_client(), Validation helpers for WhatsApp tools., Return a value the sidecar can resolve: a full chat id, or a name/number string., resolve_recipient(), validate_group_action(), Any, Any, Any (+17 more)

### Community 5 - "registry/__init__.py"
Cohesion: 0.08
Nodes (38): ABC, BaseTool, Any, Enum, str, Abstract base class for all filesystem tools. Subclasses must define ``name``,…, Perform the tool's operation. Returns a dictionary that will be wrapped in a…, RiskLevel (+30 more)

### Community 6 - "server.js"
Cohesion: 0.07
Nodes (31): dependencies, express, qrcode-terminal, venom-bot, description, main, name, scripts (+23 more)

### Community 7 - "EventType"
Cohesion: 0.19
Nodes (12): get_event_bus(), EventType, Enum, str, setup_logging(), test_events_recent_endpoint(), MockWhatsAppTool, asyncio (+4 more)

### Community 8 - "WhatsAppClient"
Cohesion: 0.09
Nodes (18): _get_creds(), _load_token_path(), Any, Credentials, Path, Return a path to a ``token.json`` if one exists next to the tool or at the…, Any, Any (+10 more)

### Community 9 - "roadmap_phase_2.md"
Cohesion: 0.06
Nodes (31): 10. Risk Levels, 11. Never Use Shell Commands for Normal File Operations, 12. Structured Tool Contract, 13. Verification, 14. Dry Run, 15. Idempotency, 16. Execution Engine, 17. Tool Registry (+23 more)

### Community 10 - "pipelines.py"
Cohesion: 0.12
Nodes (25): list_pipelines(), Any, get, post, Return a list of available pipeline names., Execute a pipeline by name with given parameters., run_pipeline(), ArchiveOldFilesPipeline (+17 more)

### Community 11 - "ServiceMemoryManager"
Cohesion: 0.17
Nodes (9): Any, Compile raw events for a given day into structured daily digests., Execute rolling cleanup according to retention policies., Manages ambient multi-service memory across WhatsApp, Gmail, and Google Drive., Retrieve recent activity events within the hot window (e.g., 24h)., Return unread counts per service within the hot window., Retrieve structured daily digests for the past N days (default 7)., Construct a high-density, structured ambient memory block for Jarvis's prompt. (+1 more)

### Community 12 - "test_gmail_tools.py"
Cohesion: 0.31
Nodes (9): ValidationError, asyncio, fixture, setup_registry(), test_send_email_happy_path_no_creds(), test_send_email_missing_attachment_fails_fast(), test_send_email_missing_params(), test_send_email_mock_mode_with_attachment() (+1 more)

### Community 13 - "ScopedToolRegistry"
Cohesion: 0.17
Nodes (7): Any, Return the tool instance if it is in the allowed set, else raise., Return only the allowed tools (name → tool instance)., Return the set of permitted tool names., A read‑only view of the global ``ToolRegistry`` that only exposes a whitelisted…, ScopedToolRegistry, TestScopedRegistry

### Community 14 - "AntigravityWorkerAgent"
Cohesion: 0.08
Nodes (32): _build_args(), _extract_session_id(), Any, Non-interactive Antigravity CLI client. Wraps `agy run` (or configured CLI) as…, Execute `agy` via stream-json stdin/stdout and collect structured results., Result of a single `agy run` invocation., Build the argument list for official Antigravity CLI (`agy.exe`)., Try to extract the Antigravity session/conversation ID from events or raw… (+24 more)

### Community 15 - "JarvisEvent"
Cohesion: 0.11
Nodes (17): AbstractEventLoop, GlobalEventBus, Queue, Central Async Event Spine for Jarvis. Supports: - Multi-subscriber SSE queue…, Explicitly set or update the main asyncio loop for cross-thread calls., Return a snapshot of recently published events in chronological order., Subscribe a new asyncio.Queue to receive live streaming events., Remove an asyncio.Queue from active SSE subscribers. (+9 more)

### Community 16 - "delete_file.py"
Cohesion: 0.22
Nodes (6): move_to_trash(), Path, Recoverable-delete support: moves items into a backend-local trash folder., Move a file or folder into the trash directory and return its new path. The…, DeleteFileTool, Any

### Community 17 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 18 - "WorkerEngine"
Cohesion: 0.15
Nodes (11): Any, Queue a parent guidance message for the worker loop., Approve the implementation plan and resume worker execution., Reject or request changes to the implementation plan with feedback., Request cooperative cancellation of the worker loop., Fork the session and start the worker loop as a background task., Orchestrates a single worker session. Lifecycle: fork (create on‑disk session)…, Run one tool step: update state, emit events, record outcome. (+3 more)

### Community 19 - "AGENTS.md — Jarvis AI Automation Backend"
Cohesion: 0.08
Nodes (23): Agent note (important), AGENTS.md — Jarvis AI Automation Backend, Architecture, Backend Conventions, DOM driver internals (`server.js`) — current WhatsApp Web realities, Gmail Module, Gotchas, Groq planning adapter (opencode) (+15 more)

### Community 20 - "AI-Automation Frontend/package.json"
Cohesion: 0.08
Nodes (23): dependencies, next, react, react-dom, devDependencies, eslint, eslint-config-next, tailwindcss (+15 more)

### Community 21 - ".analyze_prompt"
Cohesion: 0.11
Nodes (12): Any, Read the full content of JARVIS_MEMORY.md., Append an entry to the scratchpad section in JARVIS_MEMORY.md. Deduplicates…, Record activity timestamp to reset idle timer., Evaluate instant conversational intents (<5ms response time)., Build structured planning prompt with complete tool knowledge and ambient…, Safely extract JSON object from raw response text., Return required parameters for a tool from registry or fallback. (+4 more)

### Community 22 - "query"
Cohesion: 0.12
Nodes (16): _build_index(), get_index(), Any, query(), Semantic tool selector: FAISS index over tool example phrases. Loaded once at…, Encode all example phrases and build a flat FAISS inner-product (cosine) index., Return or lazily initialize the global FAISS index., Return (best_tool_name, confidence_score) for the given prompt. Returns (None,… (+8 more)

### Community 23 - "test_memory.py"
Cohesion: 0.08
Nodes (14): LongTermMemory, SQLite-backed store of durable facts (deduplicated, capped)., Add a fact. Returns False if empty or already known., Return up to ``limit`` most recent facts (oldest first)., Case-insensitive substring search over stored facts., Remove a specific fact by exact content match., Remove all facts. Returns how many were deleted., fake_agent_env() (+6 more)

### Community 24 - "resolve_path"
Cohesion: 0.07
Nodes (37): Path, Resolve a user-provided path string to an absolute Path. - Rejects empty…, resolve_path(), ensure_exists(), ensure_is_dir(), is_protected(), Path, Return True if the path is within a protected location. (+29 more)

### Community 25 - "TaskContract"
Cohesion: 0.10
Nodes (21): BaseModel, Serialize to JSON for transport (parent ↔ worker session init)., The task contract defines what a worker is expected to do, with strict…, Ensure default allowed_tools is never None., TaskContract, Create the on‑disk worker session from a contract., ActiveStreamGuardian, json_dump_safe() (+13 more)

### Community 26 - "test_agent_fork.py"
Cohesion: 0.23
Nodes (13): _fork_task(), Fork a background worker session via the workers module and record a tracked…, get_engine(), Used by the agent route to look up engines after delegation., isolated_sessions(), asyncio, fixture, test_adapter_accepts_bare_fork_step() (+5 more)

### Community 27 - "Repository"
Cohesion: 0.11
Nodes (12): ExecutionLog, 24-Hour Hot Activity Feed event for WhatsApp, Gmail, and Google Drive., 7-Day Rolling Semantic Memory digests per service., ServiceDailyDigest, ServiceEvent, Task, Any, datetime (+4 more)

### Community 28 - "OpenCodeAdapter"
Cohesion: 0.13
Nodes (14): OpenCodeAdapter, Any, Adapter to communicate with the Groq LLM and translate prompts into tool plans.…, Prompt that makes the LLM return a structured plan (or direct response)., Prompt used for single-step execution (legacy / fallback)., Send a chat-completion request from a full messages array and return content., Send a chat-completion request and return the raw content string., Parse the LLM's raw output as JSON, returning None on failure. (+6 more)

### Community 29 - "WorkerSession"
Cohesion: 0.09
Nodes (6): Path, Append a single JSON line to events.jsonl., Create the session directory and write the initial contract. Returns self for…, Manages a single worker's on-disk session state. On fork, creates the following…, WorkerSession, TestWorkerSession

### Community 30 - "ChatMemory"
Cohesion: 0.08
Nodes (19): ChatMessage, Persisted per-session chat history so conversations survive backend restarts., ChatMemory, Short-term chat memory: per-session sliding window of recent messages. Ultra-…, Load the most recent max_messages rows from DB into RAM cache., Append a message in RAM instantly and enqueue background SQLite persist., Stores the last ``max_messages`` messages per session in RAM with async SQLite…, Return a fast in-memory copy of the session's message history (<0.02ms). (+11 more)

### Community 31 - "Jarvis + OpenCode CLI Worker Architecture.md"
Cohesion: 0.10
Nodes (20): 10. Why Milestones Are Better Than One Huge Prompt, 12. Jarvis Is the Supervisor, 14. OpenCode JSON Output, 15. Headless OpenCode Server, 18. Future Worker Architecture, 19. Why OpenCode Is a Good First Worker, 21. Core Principle, 22. First Implementation Goal (+12 more)

### Community 32 - "ToolOutputViewer.js"
Cohesion: 0.12
Nodes (13): CopyButton(), DRIVE_LIST_TOOLS, DriveFilesView(), EMAIL_TOOLS, FILE_ACTION_TOOLS, FILE_CONTENT_TOOLS, FILE_LIST_TOOLS, FileContentView() (+5 more)

### Community 33 - "agent.py"
Cohesion: 0.13
Nodes (23): clear_history(), clear_memory(), _execute_plan(), _get_adapter(), get_history(), get_memory(), _learn_from_turn(), PromptRequest (+15 more)

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
Cohesion: 0.14
Nodes (7): ArtifactsPanel(), EVENT_STYLE, formatBytes(), formatEventsToTerminal(), STATUS_STYLE, WorkerPage(), poll()

### Community 42 - "TaskOrchestrator"
Cohesion: 0.21
Nodes (8): Any, Reactive Event-Driven Task Orchestrator. Allows Jarvis to chain dependent tasks…, Attach listener to the global event bus., Register a follow-up action to execute as soon as target_session_id completes., Handle worker completion and trigger all registered hooks., TaskOrchestrator, BaseModel, ReactiveHook

### Community 43 - "main.py"
Cohesion: 0.24
Nodes (10): ExecutionError, jarvis_exception_handler(), JarvisException, NotFoundError, Any, Request, create_app(), FastAPI (+2 more)

### Community 44 - "PersistentAgyDaemon"
Cohesion: 0.20
Nodes (9): PersistentAgyDaemon, Maintains a persistent, warm background Antigravity CLI process. Uses `agy…, Start or verify the persistent background daemon process., Send a turn over the persistent stdin/stdout pipe with fallback., Gracefully stop the persistent daemon., asyncio, test_persistent_daemon_ensure_running(), test_persistent_daemon_send_turn_success() (+1 more)

### Community 45 - "EventBus"
Cohesion: 0.21
Nodes (5): emit(), EventBus, Helper that gives the worker engine a clean ``await bus.xxx`` API., Send an event to all registered callbacks for *session_id*. Callbacks may be…, TestEventBus

### Community 46 - "_contract"
Cohesion: 0.22
Nodes (6): Deserialize from JSON received from the parent., _contract(), asyncio, The worker must not be able to call tools outside allowed_tools., TestTaskContract, TestWorkerEngine

### Community 47 - "test_tools_and_routes.py"
Cohesion: 0.10
Nodes (22): client(), fixture, test_unknown_worker_still_404s(), client(), fixture, engine(), asyncio, fixture (+14 more)

### Community 48 - "📦 Jarvis Direct Tool Catalog"
Cohesion: 0.13
Nodes (14): 1. 💬 WhatsApp Module Tools & Skills, 2. ✉️ Gmail Module Tools & Skills, 3. 📂 Google Drive Module Tools & Skills, 4. ⚡ Autonomous Antigravity Worker Delegation (`fork`), Antigravity Native Worker Capabilities:, 🧭 Core Architecture: Executive Orchestrator, Direct Conversational Response:, Executive Principles: (+6 more)

### Community 49 - "send_file.py"
Cohesion: 0.19
Nodes (7): ensure_is_file(), ExtractTool, Any, Any, ReadFileTool, Any, SendFileTool

### Community 50 - "DriveInboundListener"
Cohesion: 0.32
Nodes (3): DriveInboundListener, Persist drive update to SQLite service_events table., Continuous background listener that monitors Google Drive for recently modified…

### Community 51 - "service_memory.py"
Cohesion: 0.15
Nodes (8): Memory, Long-term agent memory: durable facts about the user and their preferences., Long-term memory: durable facts persisted in SQLite. These survive restarts and…, 7-Day Temporal Multi-Service Memory & 24-Hour Hot Activity Feed Manager. This…, fixture, repo(), test_events_feed_and_digest_routes(), test_service_memory_manager_prompt_builder()

### Community 52 - "ListRecentEmailsSkill"
Cohesion: 0.22
Nodes (9): ListRecentEmailsPipeline, Any, Pipeline that runs the ListRecentEmailsSkill. Demonstrates how higher‑level…, ListRecentEmailsSkill, List recent emails matching a query via Gmail API. Parameters ---------- query:…, asyncio, fixture, setup_skill() (+1 more)

### Community 53 - "WhatsAppInboundListener"
Cohesion: 0.16
Nodes (9): Any, Continuous background listener that monitors WhatsApp chats and emits digest…, Persist incoming chat preview to SQLite service_events table., Fetch and persist recent WhatsApp chats and messages into SQLite service_events…, WhatsAppInboundListener, asyncio, test_gmail_inbound_listener_emits_event(), test_whatsapp_inbound_listener_emits_event() (+1 more)

### Community 54 - "antigravity_worker/agent/milestones.py"
Cohesion: 0.09
Nodes (23): build_execution_prompt(), build_planning_prompt(), build_prompt(), build_testing_prompt(), is_simple_task(), Milestone, MilestonePhase, plan_milestones() (+15 more)

### Community 55 - "core/config.py"
Cohesion: 0.29
Nodes (6): get_health(), HealthResponse, BaseModel, get, Settings, BaseSettings

### Community 56 - "20. The Final Desired Experience"
Cohesion: 0.15
Nodes (13): 20. The Final Desired Experience, Phase 10 — Correction, Phase 11 — Final Verification, Phase 12 — Final Report, Phase 1 — Planning, Phase 2 — Worker Assignment, Phase 3 — Session Creation, Phase 4 — Milestone 1 (+5 more)

### Community 57 - "36. Development Order"
Cohesion: 0.15
Nodes (13): 36. Development Order, Step 10 — Pipelines, Step 11 — API exposure, Step 12 — End-to-end test, Step 1 — Backend foundation, Step 2 — Core architecture, Step 3 — Tool system, Step 4 — File System helpers (+5 more)

### Community 58 - "apiFetch"
Cohesion: 0.19
Nodes (14): PowerControls(), handleCancelShutdown(), handleLock(), handleShutdownConfirm(), TaskChainTracker(), checkWorkerStatus(), apiFetch(), getHeaders() (+6 more)

### Community 59 - "ExecutionEngine"
Cohesion: 0.20
Nodes (12): BaseTool Contract, ExecutionEngine, OpenCodeAdapter _KNOWN_TOOLS, Module Skeleton (skills/tools/pipelines/helpers), ToolRegistry, Session: Gmail Tools, OAuth & Agent Email Routing, Phase 2 Definition of Done, Dry Run Support (+4 more)

### Community 60 - "Jarvis Backend Implementation Log"
Cohesion: 0.17
Nodes (12): Agent can fork, Frontend, Jarvis Backend Implementation Log, Key Components Built, Session: Fork UX — agent `fork` tool, manual fork form, chat persistence (2026-09-12), Session: Jarvis + OpenCode CLI Worker Architecture & Word Worker Removal (2026-09-15), Summary, Verified end-to-end flows (+4 more)

### Community 61 - "start_service.py"
Cohesion: 0.25
Nodes (17): clean_stale_chrome_locks(), cleanup(), establish_tunnel(), is_backend_running(), is_tunnel_alive(), is_whatsapp_running(), kill_proc(), log() (+9 more)

### Community 62 - "events.py"
Cohesion: 0.13
Nodes (22): get_activity_feed(), get_feed_unread_counts(), get_recent_events(), get_seven_day_digests(), HookRegistrationRequest, ManualEventRequest, publish_manual_event(), Any (+14 more)

### Community 63 - "tasks.py"
Cohesion: 0.36
Nodes (8): create_task(), get_task(), list_tasks(), Any, get, post, Session, update_task_status()

### Community 65 - "app/page.js"
Cohesion: 0.30
Nodes (7): ActivityFeed(), loadFeed(), formatTimestamp(), API_URL, SUGGESTIONS, STATUS_STYLE, react

### Community 66 - "ExecutionEngine"
Cohesion: 0.24
Nodes (13): ExecutionEngine, Core engine that validates input, executes a tool, and returns a ToolResult.…, OrganizeDownloadsPipeline, Any, Pipeline that runs the OrganizeDownloadsSkill. It demonstrates how higher‑level…, asyncio, test_list_drive_files_mock_mode(), test_list_drive_files_no_creds() (+5 more)

### Community 67 - "execution_engine.py"
Cohesion: 0.24
Nodes (6): Any, BaseModel, Standardized result returned by any tool execution., ToolResult, asyncio, test_execution_engine_list_directory()

### Community 68 - "GmailInboundListener"
Cohesion: 0.19
Nodes (8): GmailInboundListener, _load_creds(), Any, datetime, Persist email to SQLite service_events table., Load Google OAuth credentials with multiple fallback search paths., Synchronous fetch executed in worker thread., Continuous background listener that monitors Gmail for new unread messages and…

### Community 69 - "manage_chat.py"
Cohesion: 0.18
Nodes (6): Connection states of the WhatsApp sidecar and human-readable descriptions., validate_chat_action(), GetStatusTool, Any, ManageChatTool, Any

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

### Community 78 - "JarvisBrainManager"
Cohesion: 0.16
Nodes (12): JarvisBrainManager, Path, Jarvis Central Brain Manager powered by Antigravity CLI (`agy.exe`). Features:…, Central orchestrator for Jarvis's persistent Antigravity Brain., Synthesize a complete Master Task Specification prompt for autonomous workers., Ensure JARVIS_MEMORY.md exists on disk., Antigravity module for Jarvis core brain and memory., build_master_task_prompt() (+4 more)

### Community 79 - "skills.py"
Cohesion: 0.29
Nodes (7): list_skills(), Any, get, post, Return a list of registered skills (category == "skill")., Execute a skill by name with given parameters., run_skill()

### Community 80 - "tools.py"
Cohesion: 0.29
Nodes (7): list_tools(), Any, get, post, Return a list of registered tool names and descriptions., Execute a tool by name with given parameters., run_tool()

### Community 81 - "get_service_memory_manager"
Cohesion: 0.31
Nodes (10): lifespan(), _periodic_memory_maintenance(), FastAPI, Periodic background task to aggregate daily digests and prune expired 7-day…, get_drive_listener(), get_gmail_listener(), get_service_memory_manager(), get_whatsapp_listener() (+2 more)

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

### Community 86 - "test_antigravity_brain.py"
Cohesion: 0.28
Nodes (12): asyncio, fixture, Path, Unit tests for JarvisBrainManager and living memory system., temp_memory_file(), test_brain_manager_analyze_prompt_conversational(), test_brain_manager_analyze_prompt_plan(), test_brain_manager_appends_scratchpad() (+4 more)

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

### Community 95 - "Chat.js"
Cohesion: 0.29
Nodes (3): BotMessage(), UserBubble(), ToolOutputViewer()

### Community 96 - "gmail/helpers/validation.py"
Cohesion: 0.40
Nodes (4): Validate that a search query string is non‑empty., Basic validation for an email address string. Returns True if the string looks…, validate_email_address(), validate_query()

### Community 97 - "patch"
Cohesion: 0.36
Nodes (8): asyncio, Unit tests for system power management endpoints., test_cancel_shutdown_endpoint(), test_cancel_shutdown_tool_execution(), test_restart_endpoint(), test_shutdown_endpoint(), test_shutdown_tool_execution(), patch

### Community 99 - "test_mutation_tools.py"
Cohesion: 0.60
Nodes (4): asyncio, Path, test_dry_run_create_folder(), test_mutation_tools_flow()

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

### Community 108 - "ToolRegistry"
Cohesion: 0.16
Nodes (4): AgentFactory, # NOTE: params must match each tool's ``input_schema`` exactly — the plan, Registry that holds tool classes keyed by their name. Usage: registry =…, ToolRegistry

### Community 109 - "graphify.js"
Cohesion: 0.67
Nodes (3): graphAgeDays(), GraphifyPlugin(), IMPORTANT: keep the reminder string free of backticks and $(...) constructs.

### Community 110 - "7. Tool vs Skill vs Pipeline"
Cohesion: 0.50
Nodes (4): 7. Tool vs Skill vs Pipeline, Pipeline, Skill, Tool

### Community 113 - "_load_token_path"
Cohesion: 0.25
Nodes (7): _get_creds(), _load_token_path(), Any, Credentials, Path, Load Gmail API credentials from token file or return None. Looks for…, Return credentials if present, otherwise respect ``GMAIL_MOCK``.

### Community 117 - "UnreadDigestSkill"
Cohesion: 0.28
Nodes (7): DailyDigestPipeline, Any, Run the unread digest and send it to the given chat (run on a schedule or on…, Collect all unread WhatsApp chats and their recent messages into one digest., UnreadDigestSkill, test_daily_digest_pipeline(), test_unread_digest_skill()

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

### Community 141 - "write_file.py"
Cohesion: 0.31
Nodes (7): Any, Path, verify_content(), verify_is_dir(), verify_is_file(), Any, WriteFileTool

### Community 142 - "base/bus.py"
Cohesion: 0.11
Nodes (18): Request, SSE stream of this worker's events (live activity feed with disk replay…, Real-time SSE stream of raw Antigravity CLI events (step_update deltas, tool…, worker_events(), _callback(), event_generator(), worker_stream(), stream_generator() (+10 more)

### Community 143 - "normalize_phone"
Cohesion: 0.33
Nodes (6): normalize_phone(), Normalize a phone number to bare digits (no +, spaces, or dashes)., Convert a phone number or bare number to a WhatsApp chat id ('<digits>@c.us')., to_chat_id(), test_normalize_phone(), test_to_chat_id()

### Community 144 - "Session: Gmail Tools, OAuth & Agent Email Routing (2026-09-12)"
Cohesion: 0.40
Nodes (5): Addendum: attachments + agent robustness (same day), Session: Gmail Tools, OAuth & Agent Email Routing (2026-09-12), State, Tested & fixed end-to-end (all ✅), Verified live via backend (:8000)

### Community 161 - "SendReportSkill"
Cohesion: 0.50
Nodes (4): Summarize a file or folder and send the summary as a WhatsApp message., SendReportSkill, test_send_report_skill_file(), test_send_report_skill_folder()

### Community 162 - "DownloadsNotifierPipeline"
Cohesion: 0.67
Nodes (3): DownloadsNotifierPipeline, Notify a WhatsApp chat about files that appeared in a folder recently (e.g.…, test_downloads_notifier_pipeline()

### Community 163 - "PhotoBackupPipeline"
Cohesion: 0.67
Nodes (3): PhotoBackupPipeline, Download photos from a WhatsApp chat and store them in YYYY/MM folders., test_photo_backup_pipeline()

### Community 164 - "engine"
Cohesion: 0.67
Nodes (3): engine(), fake_client(), fixture

## Knowledge Gaps
- **336 isolated node(s):** `$schema`, `plugin`, `FILE_LIST_TOOLS`, `FILE_CONTENT_TOOLS`, `FILE_ACTION_TOOLS` (+331 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 923 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ExecutionEngine` connect `ExecutionEngine` to `test_whatsapp.py`, `registry/__init__.py`, `EventType`, `test_gmail_tools.py`, `WorkerEngine`, `TaskContract`, `agent.py`, `test_file_tools_v2.py`, `engine`, `TaskOrchestrator`, `main.py`, `test_tools_and_routes.py`, `ListRecentEmailsSkill`, `execution_engine.py`, `skills.py`, `tools.py`, `test_search_content.py`, `test_mutation_tools.py`, `ToolRegistry`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `TaskContract` connect `TaskContract` to `test_opencode_worker.py`, `agent.py`, `workers.py`, `_contract`, `AntigravityWorkerAgent`, `WorkerEngine`, `test_agent_fork.py`, `WorkerSession`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `WorkerEngine` connect `WorkerEngine` to `test_opencode_worker.py`, `ExecutionEngine`, `workers.py`, `ToolRegistry`, `EventBus`, `base/bus.py`, `ScopedToolRegistry`, `AntigravityWorkerAgent`, `_contract`, `TaskContract`, `test_agent_fork.py`, `WorkerSession`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `BaseTool` (e.g. with `ExecutionEngine` and `ToolRegistry`) actually correct?**
  _`BaseTool` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 46 inferred relationships involving `RiskLevel` (e.g. with `SearchDriveSkill` and `ListDriveFilesTool`) actually correct?**
  _`RiskLevel` has 46 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `ExecutionEngine` (e.g. with `TaskOrchestrator` and `ExecutionError`) actually correct?**
  _`ExecutionEngine` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `WorkerSession` (e.g. with `clear_all_workers()` and `get_worker_artifact_file()`) actually correct?**
  _`WorkerSession` has 17 INFERRED edges - model-reasoned connections that need verification._