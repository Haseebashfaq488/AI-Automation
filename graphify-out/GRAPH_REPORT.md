# Graph Report - AI-Automation  (2026-09-26)

## Corpus Check
- 265 files · ~170,948 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 58 file(s) not represented in the graph (top: .vrma 41, (none) 5, .bat 5)

## Summary
- 2430 nodes · 4582 edges · 190 communities (142 shown, 31 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 344 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cd83eecf`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_opencode_worker.py
- test_whatsapp.py
- get_drive_service
- workers.py
- ListDirectoryTool
- VRMAvatar.js
- server.js
- TaskOrchestrator
- WhatsAppClient
- roadmap_phase_2.md
- tts.py
- ServiceMemoryManager
- get
- AvatarCanvas.js
- AntigravityWorkerAgent
- JarvisEvent
- tasks.py
- What You Must Do When Invoked
- WorkerEngine
- AGENTS.md — Jarvis AI Automation Backend
- AI-Automation Frontend/package.json
- JarvisBrainManager
- query
- test_memory.py
- resolve_path
- TaskContract
- test_agent_fork.py
- service_memory.py
- test_session_handover.py
- WorkerSession
- ChatMemory
- Jarvis + OpenCode CLI Worker Architecture.md
- ToolOutputViewer.js
- agent.py
- verify_exists
- Adding New Modules to the Jarvis Backend
- test_file_tools_v2.py
- opencode_worker/agent/milestones.py
- IMPLEMENTATION_LOG.md
- /graphify skill
- [id]/page.js
- MemoryVectorIndex
- EventType
- BaseTool
- antigravity_worker/agent/cli_client.py
- EventBus
- _contract
- test_tools_and_routes.py
- 📦 Jarvis Direct Tool Catalog
- whatsapp/helpers/validation.py
- DriveInboundListener
- get_onnx_embedder
- ToolRegistry
- ._persist_to_db
- antigravity_worker/agent/milestones.py
- ScopedToolRegistry
- 20. The Final Desired Experience
- 36. Development Order
- apiFetch
- ExecutionEngine
- Jarvis Backend Implementation Log
- start_service.py
- events.py
- FakeWhatsAppClient
- TestWorkersAPI
- `app/worker/[id]/` — Autonomous Worker Cockpit
- ExecutionEngine
- execution_engine.py
- GmailInboundListener
- .inspect_event
- poc.js
- graphify reference: extra exports and benchmark
- app/page.js
- AvatarAssistantMode
- Milestone Decomposition
- report_63292881.md
- 11. Jarvis Should Generate the Worker Prompts
- 13. Worker Status
- OrganizeDownloadsSkill
- skills.py
- tools.py
- FakeAdapter
- system.py
- run_tunnel.py
- Read operations
- VoiceInput.js
- TaskChainTracker.js
- 🧠 JARVIS LIVING MEMORY & SYSTEM CONTEXT
- OpenCodeAdapter
- graphify reference: query, path, explain
- `app/workers/` — Worker Management & Launch Dashboard
- lifecycle.py
- patch
- layout.js
- ListRecentEmailsPipeline
- `app/core/` — Core Engine, Tool Contracts & Reactive Orchestration
- gmail/helpers/validation.py
- run_antigravity_cli
- Repository
- AvatarGestures
- Worker Session
- 16. Two Possible Automation Approaches
- 17. The Planned OpenCode Worker
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- setup_drive_oauth.py
- Jarvis AI Automation — Frontend Architecture & Agent Guide
- UnreadDigestSkill
- graphify.js
- 7. Tool vs Skill vs Pipeline
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- pipelines.py
- compilerOptions
- next.config.mjs
- setup_gmail_oauth.py
- get_client
- Jarvis + OpenCode CLI Worker Architecture
- 3. OpenCode Has Two Different Ways of Being Used
- opencode.json
- 32. Testing
- 33. Safety Requirements
- Centralized Path Safety Layer
- rules/graphify.md
- extraction-spec.md
- workflows/graphify.md
- AGENTS.md — Jarvis AI Automation Frontend
- eslint.config.mjs
- postcss.config.mjs
- whatsapp/helpers/paths.py
- whatsapp/__init__.py
- antigravity_worker/__init__.py
- probe.js
- 3. Critical Invariants & Gotchas
- `app/` — FastAPI Application Shell & Lifespan
- get_event_bus
- `app/` — Application Shell & Home Chat Dashboard
- 📁 Module Structure
- worker_events
- AvatarExpression
- VRMAnimationManager
- Worker Statuses
- jarvis-backend
- `app/workers/` — Autonomous Background Worker Engine
- dependencies
- `app/api/` — HTTP & SSE API Gateway
- `app/lib/` — Networking & Shared Utilities
- AvatarBlink
- Milestone
- `app/modules/` — Domain Capabilities & Integrations
- Jarvis AI Automation — Backend Engine
- AvatarLoader
- 📦 Bubbles Historical Memory & Worker Receipt Archive
- `tests/` — Backend Automated Test Suite
- 📋 Project Handover Brief
- main.py
- TestAntigravityConfig
- _get_shared_embedder
- _load_token_path
- base/bus.py
- test_gmail_tools.py
- test_search_content.py
- DownloadsNotifierPipeline
- tool_vector_index.py
- Session: Optimizing the WhatsApp DOM Feature (2026-09-11)
- memory_vector_index.py
- AvatarPose
- .constructor
- PhotoBackupPipeline
- SemanticCueEngine
- .model_dump_json
- ._make_on_event

## God Nodes (most connected - your core abstractions)
1. `BaseTool` - 105 edges
2. `RiskLevel` - 97 edges
3. `resolve_path()` - 61 edges
4. `WorkerSession` - 59 edges
5. `ExecutionEngine` - 52 edges
6. `WorkerEngine` - 52 edges
7. `validate_path()` - 47 edges
8. `TaskContract` - 46 edges
9. `JarvisEvent` - 44 edges
10. `Repository` - 42 edges

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

## Communities (190 total, 31 thin omitted)

### Community 0 - "test_opencode_worker.py"
Cohesion: 0.06
Nodes (40): _build_args(), _extract_session_id(), Any, Non-interactive OpenCode CLI client. Wraps ``opencode run`` as an async…, Try to extract the OpenCode session ID from events or raw output., Result of a single ``opencode run`` invocation., Execute ``opencode run`` and collect structured results. Parameters ----------…, Build the ``opencode run`` argument list. (+32 more)

### Community 1 - "test_whatsapp.py"
Cohesion: 0.15
Nodes (23): Summarize a file or folder and send the summary as a WhatsApp message., SendReportSkill, asyncio, Tests for the WhatsApp module using a fake sidecar client., test_download_media_tool(), test_get_messages_tool(), test_get_recent_whatsapp_activity_tool(), test_get_unread_messages_tool() (+15 more)

### Community 2 - "get_drive_service"
Cohesion: 0.13
Nodes (18): format_file_size(), get_drive_creds(), get_drive_service(), get_token_path(), is_mock_mode(), Credentials, Path, Find drive_token.json or fallback token.json in project paths. (+10 more)

### Community 3 - "workers.py"
Cohesion: 0.08
Nodes (37): _agent_factory_for(), factory(), approve_worker_plan(), ApprovePlanRequest, cancel_worker(), clear_all_workers(), _disk_sessions(), fork_worker() (+29 more)

### Community 4 - "ListDirectoryTool"
Cohesion: 0.14
Nodes (6): AppendFileTool, Any, ListDirectoryTool, Any, Any, SearchContentTool

### Community 5 - "VRMAvatar.js"
Cohesion: 0.19
Nodes (3): AvatarBreathing, AvatarIdle, three

### Community 6 - "server.js"
Cohesion: 0.07
Nodes (31): dependencies, express, qrcode-terminal, venom-bot, description, main, name, scripts (+23 more)

### Community 7 - "TaskOrchestrator"
Cohesion: 0.14
Nodes (12): Any, Reactive Event-Driven Task Orchestrator. Allows Jarvis to chain dependent tasks…, Handle worker failure and abort registered hooks., Handle worker completion and trigger all registered hooks., Select the most relevant non-test business artifact for this specific hook., Attach listener to the global event bus., Interpolate placeholders and infer missing file/attachment arguments., Self-healing check: if worker is already finished on disk, trigger pending… (+4 more)

### Community 8 - "WhatsAppClient"
Cohesion: 0.09
Nodes (18): _get_creds(), _load_token_path(), Any, Credentials, Path, Return a path to a ``token.json`` if one exists next to the tool or at the…, Any, Any (+10 more)

### Community 9 - "roadmap_phase_2.md"
Cohesion: 0.05
Nodes (37): 10. Risk Levels, 11. Never Use Shell Commands for Normal File Operations, 12. Structured Tool Contract, 13. Verification, 14. Dry Run, 15. Idempotency, 16. Execution Engine, 17. Tool Registry (+29 more)

### Community 10 - "tts.py"
Cohesion: 0.12
Nodes (15): clean_text_for_speech(), list_recommended_voices(), BaseModel, get, post, Edge TTS (Text-to-Speech) streaming endpoint powered by Microsoft Edge Neural…, Strip delimiters, code fences, markdown, and emojis before passing to TTS., Synthesizes text into an MP3 audio stream. (+7 more)

### Community 11 - "ServiceMemoryManager"
Cohesion: 0.17
Nodes (9): Any, Compile raw events for a given day into structured daily digests., Execute rolling cleanup according to retention policies., Manages ambient multi-service memory across WhatsApp, Gmail, and Google Drive., Retrieve recent activity events within the hot window (e.g., 24h)., Return unread counts per service within the hot window., Retrieve structured daily digests for the past N days (default 7)., Construct a high-density, structured ambient memory block for Jarvis's prompt. (+1 more)

### Community 12 - "get"
Cohesion: 0.12
Nodes (16): get_worker_artifact_file(), get_worker_handover(), get_worker_plan(), get_worker_resolution(), get_worker_result(), get_worker_supervisor_status(), get_worker_test_results(), list_worker_artifacts() (+8 more)

### Community 13 - "AvatarCanvas.js"
Cohesion: 0.15
Nodes (5): AvatarCanvas(), loadModel(), AvatarChoreographer, AvatarScene, AvatarCanvas

### Community 14 - "AntigravityWorkerAgent"
Cohesion: 0.13
Nodes (19): Result of a single `agy run` invocation., RunResult, AntigravityWorkerAgent, Queue parent/manager guidance for the next turn., Autonomous agent driver powered by Antigravity CLI (`agy`) with 3-Job…, Set or update the approved implementation plan and advance to execution., Receive plan rejection with feedback and reset to planning phase., asyncio (+11 more)

### Community 15 - "JarvisEvent"
Cohesion: 0.11
Nodes (17): AbstractEventLoop, GlobalEventBus, Queue, Central Async Event Spine for Jarvis. Supports: - Multi-subscriber SSE queue…, Explicitly set or update the main asyncio loop for cross-thread calls., Return a snapshot of recently published events in chronological order., Subscribe a new asyncio.Queue to receive live streaming events., Remove an asyncio.Queue from active SSE subscribers. (+9 more)

### Community 16 - "tasks.py"
Cohesion: 0.36
Nodes (8): create_task(), get_task(), list_tasks(), Any, get, post, Session, update_task_status()

### Community 17 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 18 - "WorkerEngine"
Cohesion: 0.13
Nodes (14): Any, Queue a parent guidance message for the worker loop., Dynamically enable or disable the self-testing phase., Request cooperative cancellation of the worker loop., Fork the session and start the worker loop as a background task., Orchestrates a single worker session. Lifecycle: fork (create on‑disk session)…, Discover and collect absolute paths of generated files/artifacts in priority…, Run one tool step: update state, emit events, record outcome. (+6 more)

### Community 19 - "AGENTS.md — Jarvis AI Automation Backend"
Cohesion: 0.08
Nodes (23): Agent note (important), AGENTS.md — Jarvis AI Automation Backend, Architecture, Backend Conventions, DOM driver internals (`server.js`) — current WhatsApp Web realities, Gmail Module, Gotchas, Groq planning adapter (opencode) (+15 more)

### Community 20 - "AI-Automation Frontend/package.json"
Cohesion: 0.09
Nodes (21): devDependencies, eslint, eslint-config-next, tailwindcss, @tailwindcss/postcss, name, private, scripts (+13 more)

### Community 21 - "JarvisBrainManager"
Cohesion: 0.06
Nodes (37): get_brain_manager(), JarvisBrainManager, Any, Path, Jarvis Central Brain Manager powered by Antigravity CLI (`agy.exe`). Features:…, Ensure JARVIS_MEMORY.md exists on disk., Read the full content of JARVIS_MEMORY.md., Append an entry to the scratchpad section in JARVIS_MEMORY.md. Deduplicates… (+29 more)

### Community 22 - "query"
Cohesion: 0.17
Nodes (9): query(), Return (best_tool_name, confidence_score) for the given prompt using ONNX dot…, Paraphrased WhatsApp message prompt should match send_message with high…, Complex generative/coding task prompt should match fork with high confidence., Unread digest paraphrase should match unread_digest or get_unread_messages., Listing chats paraphrase should match list_chats., Completely unrelated text should score below threshold or return None., Vector index should build and return a valid ONNX embedding matrix with labels. (+1 more)

### Community 23 - "test_memory.py"
Cohesion: 0.08
Nodes (14): LongTermMemory, Remove all facts. Returns how many were deleted., SQLite-backed store of durable facts (deduplicated, capped)., Add a fact. Returns False if empty or already known., Return up to ``limit`` most recent facts (oldest first)., Case-insensitive substring search over stored facts., Remove a specific fact by exact content match., fake_agent_env() (+6 more)

### Community 24 - "resolve_path"
Cohesion: 0.06
Nodes (38): Path, Resolve a user-provided path string to an absolute Path. - Rejects empty…, resolve_path(), move_to_trash(), Path, Recoverable-delete support: moves items into a backend-local trash folder., Move a file or folder into the trash directory and return its new path. The…, ensure_exists() (+30 more)

### Community 25 - "TaskContract"
Cohesion: 0.18
Nodes (12): BaseModel, Ensure default allowed_tools is never None., The task contract defines what a worker is expected to do, with strict…, TaskContract, Create the on‑disk worker session from a contract., ActiveStreamGuardian, Active Stream Guardian for Worker Supervision. Monitors real-time worker…, Supervises a single worker session's real-time event stream. (+4 more)

### Community 26 - "test_agent_fork.py"
Cohesion: 0.23
Nodes (13): _fork_task(), Fork a background worker session via the workers module and record a tracked…, get_engine(), Used by the agent route to look up engines after delegation., isolated_sessions(), asyncio, fixture, test_adapter_accepts_bare_fork_step() (+5 more)

### Community 27 - "service_memory.py"
Cohesion: 0.15
Nodes (8): Memory, Long-term agent memory: durable facts about the user and their preferences., Long-term memory: durable facts persisted in SQLite. These survive restarts and…, 7-Day Temporal Multi-Service Memory & 24-Hour Hot Activity Feed Manager. This…, fixture, repo(), test_events_feed_and_digest_routes(), test_service_memory_manager_prompt_builder()

### Community 28 - "test_session_handover.py"
Cohesion: 0.12
Nodes (21): launch_worker(), Create + start a worker engine and register it for polling/SSE. Shared by the…, isolated_sessions(), asyncio, fixture, Path, Test launch_worker automatically detects existing handover in workspace., Test that graphify knowledge graph is signaled in handover section and contract. (+13 more)

### Community 29 - "WorkerSession"
Cohesion: 0.08
Nodes (8): Path, Append a single JSON line to events.jsonl., Read structured session handover brief., Write structured session handover brief., Create the session directory and write the initial contract. Returns self for…, Manages a single worker's on-disk session state. On fork, creates the following…, WorkerSession, TestWorkerSession

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
Cohesion: 0.15
Nodes (21): clear_history(), clear_memory(), _execute_plan(), _get_adapter(), get_history(), get_memory(), _learn_from_turn(), PromptRequest (+13 more)

### Community 34 - "verify_exists"
Cohesion: 0.16
Nodes (10): Any, Path, Return a verification dict confirming existence of the path., verify_content(), verify_exists(), verify_is_dir(), verify_is_file(), Any (+2 more)

### Community 35 - "Adding New Modules to the Jarvis Backend"
Cohesion: 0.09
Nodes (22): 1. Module skeleton, 2. Register the new components, 2b. Make the tool available to the AGENT (essential!), 3.1 Tools endpoint, 3.2 Pipelines endpoint, 3. Expose the module via the API, 4. Optional: Add helper imports, 5. Quick checklist (+14 more)

### Community 36 - "test_file_tools_v2.py"
Cohesion: 0.10
Nodes (37): BulkRenameTool, CopyTool, CreateFileTool, CreateFolderTool, DeleteFileTool, DeleteFolderTool, ExistsTool, Any (+29 more)

### Community 37 - "opencode_worker/agent/milestones.py"
Cohesion: 0.17
Nodes (15): build_prompt(), is_simple_task(), Milestone, MilestonePhase, plan_milestones(), plan_milestones_llm_async(), Enum, str (+7 more)

### Community 38 - "IMPLEMENTATION_LOG.md"
Cohesion: 0.16
Nodes (10): ✅ Completed Modules, Module 1 – Backend Foundation & Core Config, Module 2 – Core Tool System & Execution Engine, Session: Optimizing the WhatsApp DOM Feature, Session: Worker / Orchestrator Architecture Steps 0-1, Backend Python Dependencies (requirements.txt), Files Created, Key Decisions (+2 more)

### Community 39 - "/graphify skill"
Cohesion: 0.18
Nodes (15): graphify always-on agent rule, Add URL and watch folder reference, Extra exports and benchmark reference, Extraction subagent prompt spec, GitHub clone and cross-repo merge reference, Commit hook and CLAUDE.md integration reference, Query, path, explain reference, Video/audio transcription reference (+7 more)

### Community 40 - "[id]/page.js"
Cohesion: 0.12
Nodes (9): ToolOutputViewer(), ArtifactsPanel(), EVENT_STYLE, formatBytes(), formatEventsToTerminal(), HandoverAndGraphPanel(), STATUS_STYLE, WorkerPage() (+1 more)

### Community 41 - "MemoryVectorIndex"
Cohesion: 0.22
Nodes (12): MemoryVectorIndex, Compute keyword overlap and path boosting score., Retrieve the most relevant facts for Dum Dum's current prompt. Returns [] for…, Manages dense ONNX + lexical indexing for Bubbles' living memory., fixture, Path, Unit tests for MemoryVectorIndex on-demand semantic retrieval., sample_memory_file() (+4 more)

### Community 42 - "EventType"
Cohesion: 0.15
Nodes (12): EventType, Enum, str, setup_logging(), Continuous background listener that monitors WhatsApp chats and emits digest…, WhatsAppInboundListener, test_events_recent_endpoint(), asyncio (+4 more)

### Community 43 - "BaseTool"
Cohesion: 0.08
Nodes (41): ABC, BaseTool, Any, Enum, str, Abstract base class for all filesystem tools. Subclasses must define ``name``,…, Perform the tool's operation. Returns a dictionary that will be wrapped in a…, RiskLevel (+33 more)

### Community 44 - "antigravity_worker/agent/cli_client.py"
Cohesion: 0.15
Nodes (11): PersistentAgyDaemon, Non-interactive Antigravity CLI client. Wraps `agy run` (or configured CLI) as…, Maintains a persistent, warm background Antigravity CLI process. Uses `agy…, Start or verify the persistent background daemon process., Send a turn over the persistent stdin/stdout pipe with fallback., Gracefully stop the persistent daemon., Antigravity Agent components., asyncio (+3 more)

### Community 45 - "EventBus"
Cohesion: 0.15
Nodes (7): emit(), EventBus, Helper that gives the worker engine a clean ``await bus.xxx`` API., Send an event to all registered callbacks for *session_id*. Callbacks may be…, Approve the implementation plan and resume worker execution., Reject or request changes to the implementation plan with feedback., TestEventBus

### Community 46 - "_contract"
Cohesion: 0.22
Nodes (6): Deserialize from JSON received from the parent., _contract(), asyncio, The worker must not be able to call tools outside allowed_tools., TestTaskContract, TestWorkerEngine

### Community 47 - "test_tools_and_routes.py"
Cohesion: 0.13
Nodes (18): client(), fixture, client(), fixture, engine(), asyncio, fixture, Regression tests for tool fixes and API routes. (+10 more)

### Community 48 - "📦 Jarvis Direct Tool Catalog"
Cohesion: 0.13
Nodes (14): 1. 💬 WhatsApp Module Tools & Skills, 2. ✉️ Gmail Module Tools & Skills, 3. 📂 Google Drive Module Tools & Skills, 4. ⚡ Autonomous Antigravity Worker Delegation (`fork`), Antigravity Native Worker Capabilities:, 🧭 Core Architecture: Executive Orchestrator, Direct Conversational Response:, Executive Principles: (+6 more)

### Community 49 - "whatsapp/helpers/validation.py"
Cohesion: 0.22
Nodes (9): normalize_phone(), Validation helpers for WhatsApp tools., Normalize a phone number to bare digits (no +, spaces, or dashes)., Convert a phone number or bare number to a WhatsApp chat id ('<digits>@c.us')., to_chat_id(), validate_chat_action(), test_normalize_phone(), test_to_chat_id() (+1 more)

### Community 50 - "DriveInboundListener"
Cohesion: 0.32
Nodes (3): DriveInboundListener, Persist drive update to SQLite service_events table., Continuous background listener that monitors Google Drive for recently modified…

### Community 51 - "get_onnx_embedder"
Cohesion: 0.20
Nodes (11): get_onnx_embedder(), OnnxEmbedder, ONNX Runtime Embedder for ultra-fast, zero-overhead semantic memory retrieval.…, Singleton getter for OnnxEmbedder., Lightweight, CPU-optimized text embedder using ONNX Runtime and Fast Tokenizers., Encode text(s) into 384-dimensional dense vectors. Returns 1D array if single…, test_onnx_embedder_batch_encoding(), test_onnx_embedder_empty_input() (+3 more)

### Community 52 - "ToolRegistry"
Cohesion: 0.15
Nodes (6): AgentFactory, # NOTE: params must match each tool's ``input_schema`` exactly — the plan, Registry that holds tool classes keyed by their name. Usage: registry =…, ToolRegistry, asyncio, test_execution_engine_list_directory()

### Community 53 - "._persist_to_db"
Cohesion: 0.29
Nodes (3): Any, Persist incoming chat preview to SQLite service_events table., Fetch and persist recent WhatsApp chats and messages into SQLite service_events…

### Community 54 - "antigravity_worker/agent/milestones.py"
Cohesion: 0.17
Nodes (20): build_execution_prompt(), build_master_task_prompt(), build_planning_prompt(), build_testing_prompt(), _format_handover_section(), _living_docs_section(), MilestonePhase, Any (+12 more)

### Community 55 - "ScopedToolRegistry"
Cohesion: 0.16
Nodes (7): Any, Return the tool instance if it is in the allowed set, else raise., Return only the allowed tools (name → tool instance)., Return the set of permitted tool names., A read‑only view of the global ``ToolRegistry`` that only exposes a whitelisted…, ScopedToolRegistry, TestScopedRegistry

### Community 56 - "20. The Final Desired Experience"
Cohesion: 0.15
Nodes (13): 20. The Final Desired Experience, Phase 10 — Correction, Phase 11 — Final Verification, Phase 12 — Final Report, Phase 1 — Planning, Phase 2 — Worker Assignment, Phase 3 — Session Creation, Phase 4 — Milestone 1 (+5 more)

### Community 57 - "36. Development Order"
Cohesion: 0.15
Nodes (13): 36. Development Order, Step 10 — Pipelines, Step 11 — API exposure, Step 12 — End-to-end test, Step 1 — Backend foundation, Step 2 — Core architecture, Step 3 — Tool system, Step 4 — File System helpers (+5 more)

### Community 58 - "apiFetch"
Cohesion: 0.13
Nodes (20): ActivityFeed(), loadFeed(), formatTimestamp(), PowerControls(), handleCancelShutdown(), handleLock(), handleShutdownConfirm(), API_URL (+12 more)

### Community 59 - "ExecutionEngine"
Cohesion: 0.20
Nodes (12): BaseTool Contract, ExecutionEngine, OpenCodeAdapter _KNOWN_TOOLS, Module Skeleton (skills/tools/pipelines/helpers), ToolRegistry, Session: Gmail Tools, OAuth & Agent Email Routing, Phase 2 Definition of Done, Dry Run Support (+4 more)

### Community 60 - "Jarvis Backend Implementation Log"
Cohesion: 0.09
Nodes (23): Addendum: attachments + agent robustness (same day), Agent can fork, Bug fixes along the way, Frontend, Jarvis Backend Implementation Log, Key Components Built, Not yet done (next sessions), Session: Fork UX — agent `fork` tool, manual fork form, chat persistence (2026-09-12) (+15 more)

### Community 61 - "start_service.py"
Cohesion: 0.25
Nodes (17): clean_stale_chrome_locks(), cleanup(), establish_tunnel(), is_backend_running(), is_tunnel_alive(), is_whatsapp_running(), kill_proc(), log() (+9 more)

### Community 62 - "events.py"
Cohesion: 0.12
Nodes (26): get_activity_feed(), get_feed_unread_counts(), get_recent_events(), get_seven_day_digests(), get_task_hooks(), HookRegistrationRequest, ManualEventRequest, publish_manual_event() (+18 more)

### Community 63 - "FakeWhatsAppClient"
Cohesion: 0.12
Nodes (5): engine(), fake_client(), FakeWhatsAppClient, fixture, Records calls and returns canned sidecar responses.

### Community 65 - "`app/worker/[id]/` — Autonomous Worker Cockpit"
Cohesion: 0.18
Nodes (10): 1. Directory Role & Boundary, 2. File Inventory, 3. The 7-Tab Inspection Architecture, 4. Key Sub-Components inside `page.js`, 5. Critical Invariants & Gotchas, A. `LiveWorkerTerminal`, `app/worker/[id]/` — Autonomous Worker Cockpit, B. `PlanApprovalCard` (+2 more)

### Community 66 - "ExecutionEngine"
Cohesion: 0.23
Nodes (13): ExecutionEngine, Core engine that validates input, executes a tool, and returns a ToolResult.…, OrganizeDownloadsPipeline, Any, Pipeline that runs the OrganizeDownloadsSkill. It demonstrates how higher‑level…, asyncio, test_list_drive_files_mock_mode(), test_list_drive_files_no_creds() (+5 more)

### Community 67 - "execution_engine.py"
Cohesion: 0.17
Nodes (13): ExecutionError, jarvis_exception_handler(), JarvisException, NotFoundError, Any, Request, ValidationError, Any (+5 more)

### Community 68 - "GmailInboundListener"
Cohesion: 0.19
Nodes (8): GmailInboundListener, _load_creds(), Any, datetime, Persist email to SQLite service_events table., Load Google OAuth credentials with multiple fallback search paths., Synchronous fetch executed in worker thread., Continuous background listener that monitors Gmail for new unread messages and…

### Community 69 - ".inspect_event"
Cohesion: 0.21
Nodes (8): json_dump_safe(), Any, Identify execution of unit testing and dataflow testing suites., Return guardian health and observation status., Safe serializer to string for inspection., Inspect a stream event and return an intervention message if deviation is…, Verify that file paths manipulated by the worker remain within fs_scope., Detect repeated consecutive failures on the same command/tool.

### Community 70 - "poc.js"
Cohesion: 0.29
Nodes (9): clickSend(), isLoggedIn(), launchBrowser(), main(), path, PHONE, puppeteer, QR_SHOT (+1 more)

### Community 71 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 72 - "app/page.js"
Cohesion: 0.17
Nodes (14): BotMessage(), UserBubble(), playTTS(), setTTSMuted(), stopTTS(), generateId(), Home(), callAgent() (+6 more)

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

### Community 78 - "OrganizeDownloadsSkill"
Cohesion: 0.40
Nodes (3): OrganizeDownloadsSkill, Path, Organize files in a download directory into subfolders by file extension.…

### Community 79 - "skills.py"
Cohesion: 0.29
Nodes (7): list_skills(), Any, get, post, Return a list of registered skills (category == "skill")., Execute a skill by name with given parameters., run_skill()

### Community 80 - "tools.py"
Cohesion: 0.29
Nodes (7): list_tools(), Any, get, post, Return a list of registered tool names and descriptions., Execute a tool by name with given parameters., run_tool()

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

### Community 86 - "TaskChainTracker.js"
Cohesion: 0.58
Nodes (8): formatResultString(), isDriveTool(), isEmailTool(), isWhatsAppTool(), isWorkerTool(), matchTools(), TaskChainTracker(), checkChainStatus()

### Community 87 - "🧠 JARVIS LIVING MEMORY & SYSTEM CONTEXT"
Cohesion: 0.25
Nodes (7): 💡 Active Preferences & Habits, 📁 Active Projects & Workspaces, 📜 Core Operational Rules (Manager Persona), 🧠 JARVIS LIVING MEMORY & SYSTEM CONTEXT, 📝 Recent Scratchpad (Rolling Active Notes), 📝 Scratchpad & Temporary Notes, 👤 User Profile & Invariants

### Community 88 - "OpenCodeAdapter"
Cohesion: 0.13
Nodes (14): OpenCodeAdapter, Any, Adapter to communicate with the Groq LLM and translate prompts into tool plans.…, Prompt used for single-step execution (legacy / fallback)., Send a chat-completion request from a full messages array and return content., Send a chat-completion request and return the raw content string., Parse the LLM's raw output as JSON, returning None on failure., Phase 1 — Analyze the user's prompt and return a plan or direct response. Args:… (+6 more)

### Community 89 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 90 - "`app/workers/` — Worker Management & Launch Dashboard"
Cohesion: 0.22
Nodes (8): 1. Directory Role & Boundary, 2. File Inventory, 3. Core Features & Sub-components in `page.js`, 4. External API Contracts, 5. Critical Invariants & Gotchas, A. ForkForm (Worker Provisioning), `app/workers/` — Worker Management & Launch Dashboard, B. Worker Session Card Grid

### Community 91 - "lifecycle.py"
Cohesion: 0.31
Nodes (10): get_orchestrator(), lifespan(), FastAPI, prewarm_vector_embedder(), Pre-warm the ONNX embedder model in a background thread at startup., get_drive_listener(), get_gmail_listener(), get_whatsapp_listener() (+2 more)

### Community 92 - "patch"
Cohesion: 0.36
Nodes (8): asyncio, Unit tests for system power management endpoints., test_cancel_shutdown_endpoint(), test_cancel_shutdown_tool_execution(), test_restart_endpoint(), test_shutdown_endpoint(), test_shutdown_tool_execution(), patch

### Community 93 - "layout.js"
Cohesion: 0.40
Nodes (3): geistMono, geistSans, metadata

### Community 94 - "ListRecentEmailsPipeline"
Cohesion: 0.22
Nodes (7): ListRecentEmailsPipeline, Any, Pipeline that runs the ListRecentEmailsSkill. Demonstrates how higher‑level…, asyncio, fixture, setup_skill(), test_list_recent_emails_pipeline_no_creds()

### Community 95 - "`app/core/` — Core Engine, Tool Contracts & Reactive Orchestration"
Cohesion: 0.29
Nodes (6): 1. Directory Role & Boundary, 2. File Inventory, 3. Reactive Event Orchestrator (`app/core/events/`), 4. Universal Tool Contract (`BaseTool`), 5. Critical Invariants, `app/core/` — Core Engine, Tool Contracts & Reactive Orchestration

### Community 96 - "gmail/helpers/validation.py"
Cohesion: 0.40
Nodes (4): Validate that a search query string is non‑empty., Basic validation for an email address string. Returns True if the string looks…, validate_email_address(), validate_query()

### Community 97 - "run_antigravity_cli"
Cohesion: 0.11
Nodes (18): _build_args(), _extract_session_id(), Any, Execute `agy` via stream-json stdin/stdout and collect structured results., Build the argument list for official Antigravity CLI (`agy.exe`)., Try to extract the Antigravity session/conversation ID from events or raw…, run_antigravity_cli(), _run_subprocess_sync() (+10 more)

### Community 98 - "Repository"
Cohesion: 0.11
Nodes (12): ExecutionLog, 24-Hour Hot Activity Feed event for WhatsApp, Gmail, and Google Drive., 7-Day Rolling Semantic Memory digests per service., ServiceDailyDigest, ServiceEvent, Task, Any, datetime (+4 more)

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

### Community 108 - "UnreadDigestSkill"
Cohesion: 0.28
Nodes (7): DailyDigestPipeline, Any, Run the unread digest and send it to the given chat (run on a schedule or on…, Collect all unread WhatsApp chats and their recent messages into one digest., UnreadDigestSkill, test_daily_digest_pipeline(), test_unread_digest_skill()

### Community 109 - "graphify.js"
Cohesion: 0.67
Nodes (3): graphAgeDays(), GraphifyPlugin(), IMPORTANT: keep the reminder string free of backticks and $(...) constructs.

### Community 110 - "7. Tool vs Skill vs Pipeline"
Cohesion: 0.50
Nodes (4): 7. Tool vs Skill vs Pipeline, Pipeline, Skill, Tool

### Community 113 - "pipelines.py"
Cohesion: 0.11
Nodes (27): list_pipelines(), Any, get, post, Return a list of available pipeline names., Execute a pipeline by name with given parameters., run_pipeline(), ArchiveOldFilesPipeline (+19 more)

### Community 117 - "get_client"
Cohesion: 0.07
Nodes (23): get_client(), Return a value the sidecar can resolve: a full chat id, or a name/number string., resolve_recipient(), validate_group_action(), Any, Any, Any, DownloadMediaTool (+15 more)

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

### Community 127 - "AGENTS.md — Jarvis AI Automation Frontend"
Cohesion: 0.25
Nodes (7): 1. Project Overview & Role, 2. Navigating the Codebase: The Living Documentation Rule, 3. How to Maintain & Update Folder Documentation, 4. Frontend Engineering Invariants, AGENTS.md — Jarvis AI Automation Frontend, Living Documentation Map:, This is NOT the Next.js you know

### Community 135 - "3. Critical Invariants & Gotchas"
Cohesion: 0.25
Nodes (7): 1. Directory Role & Boundary, 2. Component Inventory, 3. Critical Invariants & Gotchas, `app/components/` — Shared Component Library, Design Consistency, EventSource (SSE) Cleanup, TaskChainTracker Polling Lifecycle

### Community 136 - "`app/` — FastAPI Application Shell & Lifespan"
Cohesion: 0.29
Nodes (6): 1. Directory Role & Boundary, 2. File Inventory, 3. Subdirectory Architecture, 4. Application Lifespan (`main.py`), 5. Critical Invariants, `app/` — FastAPI Application Shell & Lifespan

### Community 137 - "get_event_bus"
Cohesion: 0.24
Nodes (10): get_event_bus(), MockWhatsAppTool, asyncio, test_task_orchestrator_auto_discovers_workspace_file(), test_task_orchestrator_chains_worker_completion(), test_task_orchestrator_interpolates_email_attachments(), __init__(), test_task_orchestrator_multi_step_follower_pipeline() (+2 more)

### Community 140 - "`app/` — Application Shell & Home Chat Dashboard"
Cohesion: 0.25
Nodes (7): 1. Directory Role & Boundary, 2. File Inventory, 3. Subdirectory Architecture, 4. State Management & Data Flow in `page.js`, 5. External API Contracts, 6. Critical Invariants & Gotchas, `app/` — Application Shell & Home Chat Dashboard

### Community 141 - "📁 Module Structure"
Cohesion: 0.22
Nodes (9): Module 10 – Agent Memory, Module 3 – File System Safety & Path Helpers, Module 4 – Read-Only File System Tools, Module 5 – Mutation Tools & Dry-Run Engine, Module 6 – Database, Task Manager & Execution Journal, Module 7 – OpenCode (Groq) Integration Adapter, Module 8 – File System Skills & Pipelines, Module 9 – API Layer, Event Streaming & End-to-End Validation (+1 more)

### Community 142 - "worker_events"
Cohesion: 0.19
Nodes (11): Request, SSE stream of this worker's events (live activity feed with disk replay…, Real-time SSE stream of raw Antigravity CLI events (step_update deltas, tool…, worker_events(), _callback(), event_generator(), worker_stream(), stream_generator() (+3 more)

### Community 161 - "`app/workers/` — Autonomous Background Worker Engine"
Cohesion: 0.25
Nodes (7): 1. Directory Role & Boundary, 2. Directory Layout & Components, 3. The 3-Job Milestone Protocol, 4. Finalization & Handover Synthesis (`_synthesize_handover`), 5. Non-Destructive Refinement Protocol, 6. Critical Invariants & Gotchas, `app/workers/` — Autonomous Background Worker Engine

### Community 162 - "dependencies"
Cohesion: 0.25
Nodes (8): dependencies, next, @pixiv/three-vrm, @pixiv/three-vrm-animation, react, react-dom, three, vrm-mixamo-retarget

### Community 163 - "`app/api/` — HTTP & SSE API Gateway"
Cohesion: 0.33
Nodes (5): 1. Directory Role & Boundary, 2. Route Inventory (`app/api/routes/`), 3. Two-Phase Agent Architecture (`agent.py`), 4. Critical Invariants & Gotchas, `app/api/` — HTTP & SSE API Gateway

### Community 164 - "`app/lib/` — Networking & Shared Utilities"
Cohesion: 0.33
Nodes (5): 1. Directory Role & Boundary, 2. File Inventory, 3. Communication Contract, 4. Critical Invariants & Gotchas, `app/lib/` — Networking & Shared Utilities

### Community 166 - "Milestone"
Cohesion: 0.25
Nodes (8): build_prompt(), is_simple_task(), Milestone, plan_milestones(), Build the prompt for the Antigravity agent milestone., A single discrete unit of work executed by the Antigravity worker., Detect if an objective is simple enough to complete in 1 execution step + 1…, Generate proportional milestone sequence with a fixed final test phase.

### Community 167 - "`app/modules/` — Domain Capabilities & Integrations"
Cohesion: 0.33
Nodes (5): 1. Directory Role & Boundary, 2. Module Inventory, 3. Module Internal Layout Convention, 4. Critical Invariants & Gotchas, `app/modules/` — Domain Capabilities & Integrations

### Community 168 - "Jarvis AI Automation — Backend Engine"
Cohesion: 0.33
Nodes (6): 1. Overview & Architecture, 2. Directory Map, 3. Environment Variables & Configuration, 4. Runbook & Common Commands, 5. Critical Invariants, Jarvis AI Automation — Backend Engine

### Community 171 - "`tests/` — Backend Automated Test Suite"
Cohesion: 0.33
Nodes (5): 1. Directory Role & Boundary, 2. Test Suite Inventory (`tests/unit/`), 3. Running Tests, 4. Testing Conventions & Mocking, `tests/` — Backend Automated Test Suite

### Community 172 - "📋 Project Handover Brief"
Cohesion: 0.50
Nodes (3): 📂 Folder-Level Documentation, 📁 Key Files & Artifacts, 📋 Project Handover Brief

### Community 173 - "main.py"
Cohesion: 0.14
Nodes (14): get_health(), HealthResponse, BaseModel, get, Settings, create_app(), FastAPI, test_unknown_worker_still_404s() (+6 more)

### Community 175 - "_get_shared_embedder"
Cohesion: 0.20
Nodes (6): _get_shared_embedder(), Any, Path, Try loading ONNX embedder singleton., Re-read JARVIS_MEMORY.md and rebuild the semantic index., Extract bullet points from memory sections (skipping invariants & profile).

### Community 176 - "_load_token_path"
Cohesion: 0.25
Nodes (7): _get_creds(), _load_token_path(), Any, Credentials, Path, Load Gmail API credentials from token file or return None. Looks for…, Return credentials if present, otherwise respect ``GMAIL_MOCK``.

### Community 177 - "base/bus.py"
Cohesion: 0.25
Nodes (8): emit_to_queues(), Any, Queue, Subscribe a new asyncio.Queue to receive live streaming events for session_id., Unsubscribe and remove an asyncio.Queue from session_id's active subscribers., Forward a streaming event to all active async queues subscribed to session_id…, subscribe(), unsubscribe()

### Community 178 - "test_gmail_tools.py"
Cohesion: 0.33
Nodes (8): asyncio, fixture, setup_registry(), test_send_email_happy_path_no_creds(), test_send_email_missing_attachment_fails_fast(), test_send_email_missing_params(), test_send_email_mock_mode_with_attachment(), test_send_email_with_missing_creds_error()

### Community 179 - "test_search_content.py"
Cohesion: 0.38
Nodes (6): engine(), asyncio, fixture, test_search_content_case_sensitive_and_non_recursive(), test_search_content_finds_matches(), test_search_content_single_file_and_max_results()

### Community 180 - "DownloadsNotifierPipeline"
Cohesion: 0.67
Nodes (3): DownloadsNotifierPipeline, Notify a WhatsApp chat about files that appeared in a folder recently (e.g.…, test_downloads_notifier_pipeline()

### Community 181 - "tool_vector_index.py"
Cohesion: 0.28
Nodes (7): _build_index(), get_index(), Any, Semantic tool selector: FAISS index over tool example phrases. Loaded once at…, Encode all example phrases with ONNX embedder into a normalized NumPy matrix., Return or lazily initialize the global ONNX tool index matrix., Unit tests for FAISS vector tool selection.

### Community 182 - "Session: Optimizing the WhatsApp DOM Feature (2026-09-11)"
Cohesion: 0.33
Nodes (6): Context, Known limitations, Optimization plan (accepted next steps, not yet implemented), Root causes found & fixed (live debugging against real WhatsApp Web), Session: Optimizing the WhatsApp DOM Feature (2026-09-11), Verified live (through backend `:8000`, all ✅)

### Community 183 - "memory_vector_index.py"
Cohesion: 0.33
Nodes (4): Lazy-loaded MemoryVectorIndex for semantic on-demand retrieval., get_memory_vector_index(), Semantic memory retriever: Ultra-low latency ONNX + Keyword index over living…, Return the global MemoryVectorIndex instance.

### Community 186 - "PhotoBackupPipeline"
Cohesion: 0.67
Nodes (3): PhotoBackupPipeline, Download photos from a WhatsApp chat and store them in YYYY/MM folders., test_photo_backup_pipeline()

### Community 189 - "._make_on_event"
Cohesion: 0.29
Nodes (3): Any, Record step result into agent history., Create a real-time event forwarder for SSE consumers.

## Knowledge Gaps
- **409 isolated node(s):** `$schema`, `plugin`, `FILE_LIST_TOOLS`, `FILE_CONTENT_TOOLS`, `FILE_ACTION_TOOLS` (+404 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1098 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ExecutionEngine` connect `ExecutionEngine` to `agent.py`, `test_whatsapp.py`, `execution_engine.py`, `test_file_tools_v2.py`, `TaskOrchestrator`, `EventType`, `BaseTool`, `skills.py`, `tools.py`, `test_tools_and_routes.py`, `WorkerEngine`, `test_gmail_tools.py`, `ToolRegistry`, `test_search_content.py`, `TaskContract`, `ListRecentEmailsPipeline`, `FakeWhatsAppClient`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `BaseTool` connect `BaseTool` to `test_whatsapp.py`, `ExecutionEngine`, `execution_engine.py`, `ListDirectoryTool`, `test_file_tools_v2.py`, `verify_exists`, `get_event_bus`, `UnreadDigestSkill`, `OrganizeDownloadsSkill`, `ToolRegistry`, `get_client`, `resolve_path`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `WorkerEngine` connect `WorkerEngine` to `test_opencode_worker.py`, `ExecutionEngine`, `workers.py`, `test_file_tools_v2.py`, `EventBus`, `worker_events`, `AntigravityWorkerAgent`, `_contract`, `ToolRegistry`, `ScopedToolRegistry`, `TaskContract`, `test_agent_fork.py`, `test_session_handover.py`, `WorkerSession`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `BaseTool` (e.g. with `ExecutionEngine` and `ToolRegistry`) actually correct?**
  _`BaseTool` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 48 inferred relationships involving `RiskLevel` (e.g. with `SearchDriveSkill` and `ListDriveFilesTool`) actually correct?**
  _`RiskLevel` has 48 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `WorkerSession` (e.g. with `approve_worker_plan()` and `clear_all_workers()`) actually correct?**
  _`WorkerSession` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `ExecutionEngine` (e.g. with `TaskOrchestrator` and `ExecutionError`) actually correct?**
  _`ExecutionEngine` has 26 INFERRED edges - model-reasoned connections that need verification._