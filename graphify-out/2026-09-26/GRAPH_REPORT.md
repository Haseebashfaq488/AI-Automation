# Graph Report - AI-Automation  (2026-09-26)

## Corpus Check
- 269 files · ~179,518 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 61 file(s) not represented in the graph (top: .vrma 42, (none) 5, .bat 5)

## Summary
- 2482 nodes · 4673 edges · 185 communities (139 shown, 29 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 347 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a238049c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_opencode_worker.py
- test_whatsapp.py
- get_drive_service
- send_file.py
- get
- VRMAvatar.js
- server.js
- TaskOrchestrator
- execution_engine.py
- roadmap_phase_2.md
- test_tts_api.py
- .build_brain_context_prompt
- OrganizeDownloadsSkill
- AvatarCanvas.js
- get_event_bus
- JarvisEvent
- tasks.py
- What You Must Do When Invoked
- WorkerEngine
- AGENTS.md — Jarvis AI Automation Backend
- AI-Automation Frontend/package.json
- JarvisBrainManager
- query
- LongTermMemory
- resolve_path
- ToolRegistry
- test_agent_fork.py
- get_service_memory_manager
- 1. Module skeleton
- WorkerSession
- ChatMemory
- Jarvis + OpenCode CLI Worker Architecture.md
- ToolOutputViewer.js
- agent.py
- TaskContract
- Adding New Modules to the Jarvis Backend
- test_file_tools_v2.py
- opencode_worker/agent/milestones.py
- IMPLEMENTATION_LOG.md
- /graphify skill
- [id]/page.js
- MemoryVectorIndex
- Session: Gmail Tools, OAuth & Agent Email Routing (2026-09-12)
- 2b. Make the tool available to the AGENT (essential!)
- PersistentAgyDaemon
- EventBus
- _contract
- test_tools_and_routes.py
- 📦 Jarvis Direct Tool Catalog
- Module 1 – Backend Foundation & Core Config
- manage_chat.py
- get_onnx_embedder
- test_search_content.py
- patch
- test_session_handover.py
- ScopedToolRegistry
- 20. The Final Desired Experience
- 36. Development Order
- apiFetch
- ExecutionEngine
- Jarvis Backend Implementation Log
- start_service.py
- Any
- `app/components/avatar/` — 3D VRM Avatar & Mocap Engine
- TestWorkersAPI
- `app/worker/[id]/` — Autonomous Worker Cockpit
- ExecutionEngine
- GmailInboundListener
- ListRecentEmailsSkill
- poc.js
- graphify reference: extra exports and benchmark
- app/page.js
- AvatarAssistantMode
- Milestone Decomposition
- report_63292881.md
- 11. Jarvis Should Generate the Worker Prompts
- 13. Worker Status
- 3. Control Deck Tabs & Capabilities
- skills.py
- tools.py
- test_memory.py
- system.py
- run_tunnel.py
- Read operations
- TaskChainTracker.js
- 🧠 JARVIS LIVING MEMORY & SYSTEM CONTEXT
- OpenCodeAdapter
- graphify reference: query, path, explain
- `app/workers/` — Worker Management & Launch Dashboard
- lifecycle.py
- layout.js
- `app/core/` — Core Engine, Tool Contracts & Reactive Orchestration
- gmail/helpers/validation.py
- AntigravityWorkerAgent
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
- Session: Worker / Orchestrator Architecture — Steps 0–1 (2026-09-12)
- graphify.js
- 7. Tool vs Skill vs Pipeline
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- list_pipelines
- compilerOptions
- next.config.mjs
- setup_gmail_oauth.py
- BaseTool
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
- EventType
- `app/` — Application Shell & Home Chat Dashboard
- 📁 Module Structure
- worker_events
- Worker Statuses
- jarvis-backend
- `app/workers/` — Autonomous Background Worker Engine
- `app/api/` — HTTP & SSE API Gateway
- `app/lib/` — Networking & Shared Utilities
- AvatarBlink
- verify_content
- `app/modules/` — Domain Capabilities & Integrations
- Jarvis AI Automation — Backend Engine
- WhatsAppInboundListener
- 📦 Bubbles Historical Memory & Worker Receipt Archive
- `tests/` — Backend Automated Test Suite
- 📋 Project Handover Brief
- _load_token_path
- _get_shared_embedder
- workers.py
- main.py
- FakeWhatsAppClient
- base/bus.py
- tool_vector_index.py
- Session: Optimizing the WhatsApp DOM Feature (2026-09-11)
- memory_vector_index.py
- core/config.py
- SemanticCueEngine
- TestAntigravityConfig
- .execute
- .__init__
- organize_downloads_pipeline.py
- ListDirectoryTool
- Phase 2 — Backend + File System Module
- 39. Instructions to the Implementing LLM
- 3. Technology Stack

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

## Communities (185 total, 29 thin omitted)

### Community 0 - "test_opencode_worker.py"
Cohesion: 0.06
Nodes (40): _build_args(), _extract_session_id(), Any, Non-interactive OpenCode CLI client. Wraps ``opencode run`` as an async…, Try to extract the OpenCode session ID from events or raw output., Result of a single ``opencode run`` invocation., Execute ``opencode run`` and collect structured results. Parameters ----------…, Build the ``opencode run`` argument list. (+32 more)

### Community 1 - "test_whatsapp.py"
Cohesion: 0.06
Nodes (50): normalize_phone(), Validation helpers for WhatsApp tools., Normalize a phone number to bare digits (no +, spaces, or dashes)., Convert a phone number or bare number to a WhatsApp chat id ('<digits>@c.us')., Return a value the sidecar can resolve: a full chat id, or a name/number string., resolve_recipient(), to_chat_id(), validate_group_action() (+42 more)

### Community 2 - "get_drive_service"
Cohesion: 0.12
Nodes (18): format_file_size(), get_drive_creds(), get_drive_service(), get_token_path(), is_mock_mode(), Credentials, Path, Find drive_token.json or fallback token.json in project paths. (+10 more)

### Community 3 - "send_file.py"
Cohesion: 0.13
Nodes (11): move_to_trash(), Path, Recoverable-delete support: moves items into a backend-local trash folder., Move a file or folder into the trash directory and return its new path. The…, ensure_is_file(), DeleteFileTool, Any, Any (+3 more)

### Community 4 - "get"
Cohesion: 0.12
Nodes (16): get_worker_artifact_file(), get_worker_handover(), get_worker_plan(), get_worker_resolution(), get_worker_result(), get_worker_supervisor_status(), get_worker_test_results(), list_worker_artifacts() (+8 more)

### Community 5 - "VRMAvatar.js"
Cohesion: 0.10
Nodes (7): AvatarBreathing, AvatarExpression, AvatarGaze, AvatarIdle, AvatarPose, VRMAvatar, three

### Community 6 - "server.js"
Cohesion: 0.07
Nodes (31): dependencies, express, qrcode-terminal, venom-bot, description, main, name, scripts (+23 more)

### Community 7 - "TaskOrchestrator"
Cohesion: 0.14
Nodes (12): Any, Reactive Event-Driven Task Orchestrator. Allows Jarvis to chain dependent tasks…, Handle worker failure and abort registered hooks., Handle worker completion and trigger all registered hooks., Select the most relevant non-test business artifact for this specific hook., Attach listener to the global event bus., Interpolate placeholders and infer missing file/attachment arguments., Self-healing check: if worker is already finished on disk, trigger pending… (+4 more)

### Community 8 - "execution_engine.py"
Cohesion: 0.24
Nodes (6): Any, BaseModel, Standardized result returned by any tool execution., ToolResult, asyncio, test_execution_engine_list_directory()

### Community 9 - "roadmap_phase_2.md"
Cohesion: 0.06
Nodes (31): 10. Risk Levels, 11. Never Use Shell Commands for Normal File Operations, 12. Structured Tool Contract, 13. Verification, 14. Dry Run, 15. Idempotency, 16. Execution Engine, 17. Tool Registry (+23 more)

### Community 10 - "test_tts_api.py"
Cohesion: 0.11
Nodes (16): clean_text_for_speech(), list_recommended_voices(), BaseModel, get, post, Edge TTS (Text-to-Speech) streaming endpoint powered by Microsoft Edge Neural…, Returns curated list of recommended voices for Jarvis / Bubbles., Strip delimiters, emojis, code fences, and markdown formatting before passing… (+8 more)

### Community 11 - ".build_brain_context_prompt"
Cohesion: 0.28
Nodes (5): Any, Retrieve recent activity events within the hot window (e.g., 24h)., Return unread counts per service within the hot window., Retrieve structured daily digests for the past N days (default 7)., Construct a high-density, structured ambient memory block for Jarvis's prompt.

### Community 12 - "OrganizeDownloadsSkill"
Cohesion: 0.33
Nodes (4): OrganizeDownloadsSkill, Any, Path, Organize files in a download directory into subfolders by file extension.…

### Community 13 - "AvatarCanvas.js"
Cohesion: 0.10
Nodes (9): AvatarCanvas, AvatarCanvas(), loadModel(), AvatarChoreographer, AvatarLoader, AvatarScene, getCurrentAudio(), AvatarCanvas (+1 more)

### Community 14 - "get_event_bus"
Cohesion: 0.24
Nodes (10): get_event_bus(), MockWhatsAppTool, asyncio, test_task_orchestrator_auto_discovers_workspace_file(), test_task_orchestrator_chains_worker_completion(), test_task_orchestrator_interpolates_email_attachments(), __init__(), test_task_orchestrator_multi_step_follower_pipeline() (+2 more)

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
Cohesion: 0.12
Nodes (15): Any, Queue a parent guidance message for the worker loop., Dynamically enable or disable the self-testing phase., Request cooperative cancellation of the worker loop., Fork the session and start the worker loop as a background task., Orchestrates a single worker session. Lifecycle: fork (create on‑disk session)…, Discover and collect absolute paths of generated files/artifacts in priority…, Run one tool step: update state, emit events, record outcome. (+7 more)

### Community 19 - "AGENTS.md — Jarvis AI Automation Backend"
Cohesion: 0.08
Nodes (23): Agent note (important), AGENTS.md — Jarvis AI Automation Backend, Architecture, Backend Conventions, DOM driver internals (`server.js`) — current WhatsApp Web realities, Gmail Module, Gotchas, Groq planning adapter (opencode) (+15 more)

### Community 20 - "AI-Automation Frontend/package.json"
Cohesion: 0.06
Nodes (30): VRMAnimationManager, dependencies, next, @pixiv/three-vrm, @pixiv/three-vrm-animation, react, react-dom, three (+22 more)

### Community 21 - "JarvisBrainManager"
Cohesion: 0.07
Nodes (33): JarvisBrainManager, Any, Path, Ensure JARVIS_MEMORY.md exists on disk., Read the full content of JARVIS_MEMORY.md., Append an entry to the scratchpad section in JARVIS_MEMORY.md. Deduplicates…, Record activity timestamp to reset idle timer., Evaluate instant conversational intents (<5ms response time). (+25 more)

### Community 22 - "query"
Cohesion: 0.17
Nodes (9): query(), Return (best_tool_name, confidence_score) for the given prompt using ONNX dot…, Paraphrased WhatsApp message prompt should match send_message with high…, Complex generative/coding task prompt should match fork with high confidence., Unread digest paraphrase should match unread_digest or get_unread_messages., Listing chats paraphrase should match list_chats., Completely unrelated text should score below threshold or return None., Vector index should build and return a valid ONNX embedding matrix with labels. (+1 more)

### Community 23 - "LongTermMemory"
Cohesion: 0.10
Nodes (12): Memory, Long-term agent memory: durable facts about the user and their preferences., LongTermMemory, Remove all facts. Returns how many were deleted., SQLite-backed store of durable facts (deduplicated, capped)., Add a fact. Returns False if empty or already known., Return up to ``limit`` most recent facts (oldest first)., Case-insensitive substring search over stored facts. (+4 more)

### Community 24 - "resolve_path"
Cohesion: 0.06
Nodes (52): Path, Resolve a user-provided path string to an absolute Path. - Rejects empty…, resolve_path(), ensure_exists(), ensure_is_dir(), is_protected(), Path, Return True if the path is within a protected location. (+44 more)

### Community 25 - "ToolRegistry"
Cohesion: 0.13
Nodes (11): AgentFactory, # NOTE: params must match each tool's ``input_schema`` exactly — the plan, Registry that holds tool classes keyed by their name. Usage: registry =…, ToolRegistry, asyncio, When a plan is rejected with feedback, the worker should re-enter planning…, When plan is approved with edited markdown, it must be written to…, When skip_testing is True, worker finishes after Job 2 without entering Job 3. (+3 more)

### Community 26 - "test_agent_fork.py"
Cohesion: 0.16
Nodes (17): _execute_plan(), _fork_task(), Execute plan steps sequentially and return collected results., Fork a background worker session via the workers module and record a tracked…, get_engine(), Used by the agent route to look up engines after delegation., Any, Execute a worker fork via the workers router / engine. (+9 more)

### Community 27 - "get_service_memory_manager"
Cohesion: 0.14
Nodes (10): Long-term memory: durable facts persisted in SQLite. These survive restarts and…, get_service_memory_manager(), 7-Day Temporal Multi-Service Memory & 24-Hour Hot Activity Feed Manager. This…, Compile raw events for a given day into structured daily digests., Execute rolling cleanup according to retention policies., Manages ambient multi-service memory across WhatsApp, Gmail, and Google Drive., ServiceMemoryManager, fixture (+2 more)

### Community 28 - "1. Module skeleton"
Cohesion: 0.40
Nodes (5): 1. Module skeleton, Helper example (`helpers/validation.py`), Minimal pipeline example (`pipelines/list_recent_emails_pipeline.py`), Minimal skill example (`skills/list_recent_emails.py`), Minimal tool example (`tools/send_email_tool.py`)

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
Cohesion: 0.13
Nodes (22): clear_history(), clear_memory(), _get_adapter(), get_history(), get_memory(), _learn_from_turn(), PromptRequest, Any (+14 more)

### Community 34 - "TaskContract"
Cohesion: 0.11
Nodes (20): BaseModel, Ensure default allowed_tools is never None., Serialize to JSON for transport (parent ↔ worker session init)., The task contract defines what a worker is expected to do, with strict…, TaskContract, ActiveStreamGuardian, json_dump_safe(), Any (+12 more)

### Community 35 - "Adding New Modules to the Jarvis Backend"
Cohesion: 0.14
Nodes (13): 2. Register the new components, 3.1 Tools endpoint, 3.2 Pipelines endpoint, 3. Expose the module via the API, 4. Optional: Add helper imports, 5. Quick checklist, 6. Conventions to keep in sync, 7. Write unit tests (+5 more)

### Community 36 - "test_file_tools_v2.py"
Cohesion: 0.08
Nodes (39): AppendFileTool, Any, BulkRenameTool, CopyTool, CreateFileTool, CreateFolderTool, DeleteFolderTool, ExistsTool (+31 more)

### Community 37 - "opencode_worker/agent/milestones.py"
Cohesion: 0.17
Nodes (15): build_prompt(), is_simple_task(), Milestone, MilestonePhase, plan_milestones(), plan_milestones_llm_async(), Enum, str (+7 more)

### Community 38 - "IMPLEMENTATION_LOG.md"
Cohesion: 0.24
Nodes (6): ✅ Completed Modules, Module 1 – Backend Foundation & Core Config, Module 2 – Core Tool System & Execution Engine, Session: Optimizing the WhatsApp DOM Feature, Session: Worker / Orchestrator Architecture Steps 0-1, Backend Python Dependencies (requirements.txt)

### Community 39 - "/graphify skill"
Cohesion: 0.18
Nodes (15): graphify always-on agent rule, Add URL and watch folder reference, Extra exports and benchmark reference, Extraction subagent prompt spec, GitHub clone and cross-repo merge reference, Commit hook and CLAUDE.md integration reference, Query, path, explain reference, Video/audio transcription reference (+7 more)

### Community 40 - "[id]/page.js"
Cohesion: 0.09
Nodes (13): ToolOutputViewer(), playAudioCue(), SUPPORTED_LANGUAGES, useSpeechRecognition(), VoiceInput(), ArtifactsPanel(), EVENT_STYLE, formatBytes() (+5 more)

### Community 41 - "MemoryVectorIndex"
Cohesion: 0.22
Nodes (12): MemoryVectorIndex, Compute keyword overlap and path boosting score., Retrieve the most relevant facts for Dum Dum's current prompt. Returns [] for…, Manages dense ONNX + lexical indexing for Bubbles' living memory., fixture, Path, Unit tests for MemoryVectorIndex on-demand semantic retrieval., sample_memory_file() (+4 more)

### Community 42 - "Session: Gmail Tools, OAuth & Agent Email Routing (2026-09-12)"
Cohesion: 0.40
Nodes (5): Addendum: attachments + agent robustness (same day), Session: Gmail Tools, OAuth & Agent Email Routing (2026-09-12), State, Tested & fixed end-to-end (all ✅), Verified live via backend (:8000)

### Community 43 - "2b. Make the tool available to the AGENT (essential!)"
Cohesion: 0.50
Nodes (4): 2b. Make the tool available to the AGENT (essential!), Adapter file: `app/modules/opencode/adapter.py`, Rules that bite if ignored, Verify the agent can plan with the new tool

### Community 44 - "PersistentAgyDaemon"
Cohesion: 0.20
Nodes (9): PersistentAgyDaemon, Maintains a persistent, warm background Antigravity CLI process. Uses `agy…, Start or verify the persistent background daemon process., Send a turn over the persistent stdin/stdout pipe with fallback., Gracefully stop the persistent daemon., asyncio, test_persistent_daemon_ensure_running(), test_persistent_daemon_send_turn_success() (+1 more)

### Community 45 - "EventBus"
Cohesion: 0.15
Nodes (7): emit(), EventBus, Helper that gives the worker engine a clean ``await bus.xxx`` API., Send an event to all registered callbacks for *session_id*. Callbacks may be…, Approve the implementation plan and resume worker execution., Reject or request changes to the implementation plan with feedback., TestEventBus

### Community 46 - "_contract"
Cohesion: 0.22
Nodes (6): Deserialize from JSON received from the parent., _contract(), asyncio, The worker must not be able to call tools outside allowed_tools., TestTaskContract, TestWorkerEngine

### Community 47 - "test_tools_and_routes.py"
Cohesion: 0.11
Nodes (20): client(), fixture, test_unknown_worker_still_404s(), client(), fixture, test_events_feed_and_digest_routes(), engine(), asyncio (+12 more)

### Community 48 - "📦 Jarvis Direct Tool Catalog"
Cohesion: 0.13
Nodes (14): 1. 💬 WhatsApp Module Tools & Skills, 2. ✉️ Gmail Module Tools & Skills, 3. 📂 Google Drive Module Tools & Skills, 4. ⚡ Autonomous Antigravity Worker Delegation (`fork`), Antigravity Native Worker Capabilities:, 🧭 Core Architecture: Executive Orchestrator, Direct Conversational Response:, Executive Principles: (+6 more)

### Community 49 - "Module 1 – Backend Foundation & Core Config"
Cohesion: 0.50
Nodes (4): Files Created, Key Decisions, Module 1 – Backend Foundation & Core Config, Next Steps

### Community 50 - "manage_chat.py"
Cohesion: 0.25
Nodes (5): Connection states of the WhatsApp sidecar and human-readable descriptions., validate_chat_action(), ManageChatTool, Any, test_validate_chat_action()

### Community 51 - "get_onnx_embedder"
Cohesion: 0.20
Nodes (11): get_onnx_embedder(), OnnxEmbedder, ONNX Runtime Embedder for ultra-fast, zero-overhead semantic memory retrieval.…, Singleton getter for OnnxEmbedder., Lightweight, CPU-optimized text embedder using ONNX Runtime and Fast Tokenizers., Encode text(s) into 384-dimensional dense vectors. Returns 1D array if single…, test_onnx_embedder_batch_encoding(), test_onnx_embedder_empty_input() (+3 more)

### Community 52 - "test_search_content.py"
Cohesion: 0.38
Nodes (6): engine(), asyncio, fixture, test_search_content_case_sensitive_and_non_recursive(), test_search_content_finds_matches(), test_search_content_single_file_and_max_results()

### Community 53 - "patch"
Cohesion: 0.36
Nodes (8): asyncio, Unit tests for system power management endpoints., test_cancel_shutdown_endpoint(), test_cancel_shutdown_tool_execution(), test_restart_endpoint(), test_shutdown_endpoint(), test_shutdown_tool_execution(), patch

### Community 54 - "test_session_handover.py"
Cohesion: 0.06
Nodes (49): build_execution_prompt(), build_master_task_prompt(), build_planning_prompt(), build_prompt(), build_testing_prompt(), _format_handover_section(), is_simple_task(), _living_docs_section() (+41 more)

### Community 55 - "ScopedToolRegistry"
Cohesion: 0.17
Nodes (7): Any, Return the tool instance if it is in the allowed set, else raise., Return only the allowed tools (name → tool instance)., Return the set of permitted tool names., A read‑only view of the global ``ToolRegistry`` that only exposes a whitelisted…, ScopedToolRegistry, TestScopedRegistry

### Community 56 - "20. The Final Desired Experience"
Cohesion: 0.15
Nodes (13): 20. The Final Desired Experience, Phase 10 — Correction, Phase 11 — Final Verification, Phase 12 — Final Report, Phase 1 — Planning, Phase 2 — Worker Assignment, Phase 3 — Session Creation, Phase 4 — Milestone 1 (+5 more)

### Community 57 - "36. Development Order"
Cohesion: 0.15
Nodes (13): 36. Development Order, Step 10 — Pipelines, Step 11 — API exposure, Step 12 — End-to-end test, Step 1 — Backend foundation, Step 2 — Core architecture, Step 3 — Tool system, Step 4 — File System helpers (+5 more)

### Community 58 - "apiFetch"
Cohesion: 0.15
Nodes (18): ActivityFeed(), loadFeed(), formatTimestamp(), PowerControls(), handleCancelShutdown(), handleLock(), handleShutdownConfirm(), API_URL (+10 more)

### Community 59 - "ExecutionEngine"
Cohesion: 0.20
Nodes (12): BaseTool Contract, ExecutionEngine, OpenCodeAdapter _KNOWN_TOOLS, Module Skeleton (skills/tools/pipelines/helpers), ToolRegistry, Session: Gmail Tools, OAuth & Agent Email Routing, Phase 2 Definition of Done, Dry Run Support (+4 more)

### Community 60 - "Jarvis Backend Implementation Log"
Cohesion: 0.17
Nodes (12): Agent can fork, Frontend, Jarvis Backend Implementation Log, Key Components Built, Session: Fork UX — agent `fork` tool, manual fork form, chat persistence (2026-09-12), Session: Jarvis + OpenCode CLI Worker Architecture & Word Worker Removal (2026-09-15), Summary, Verified end-to-end flows (+4 more)

### Community 61 - "start_service.py"
Cohesion: 0.25
Nodes (17): clean_stale_chrome_locks(), cleanup(), establish_tunnel(), is_backend_running(), is_tunnel_alive(), is_whatsapp_running(), kill_proc(), log() (+9 more)

### Community 62 - "Any"
Cohesion: 0.18
Nodes (13): get_activity_feed(), get_feed_unread_counts(), get_recent_events(), get_seven_day_digests(), Any, get, Request, Multi-subscriber Server-Sent Events (SSE) stream. (+5 more)

### Community 63 - "`app/components/avatar/` — 3D VRM Avatar & Mocap Engine"
Cohesion: 0.18
Nodes (10): 1. Directory Role & Boundary, 2. File Inventory & Responsibilities, 3. Delimiter Syntax & Speech Choreography Pipeline, 4. Critical Invariants & Gotchas, 5. Catalog of Supported Animations (43 Mocaps), `app/components/avatar/` — 3D VRM Avatar & Mocap Engine, Choreography Flow:, Preventing VRM Reload on Re-Render (+2 more)

### Community 65 - "`app/worker/[id]/` — Autonomous Worker Cockpit"
Cohesion: 0.18
Nodes (10): 1. Directory Role & Boundary, 2. File Inventory, 3. The 7-Tab Inspection Architecture, 4. Key Sub-Components inside `page.js`, 5. Critical Invariants & Gotchas, A. `LiveWorkerTerminal`, `app/worker/[id]/` — Autonomous Worker Cockpit, B. `PlanApprovalCard` (+2 more)

### Community 66 - "ExecutionEngine"
Cohesion: 0.22
Nodes (19): ValidationError, ExecutionEngine, Core engine that validates input, executes a tool, and returns a ToolResult.…, asyncio, test_list_drive_files_mock_mode(), test_list_drive_files_no_creds(), test_read_drive_file_missing_id(), test_read_drive_file_mock_mode() (+11 more)

### Community 68 - "GmailInboundListener"
Cohesion: 0.19
Nodes (8): GmailInboundListener, _load_creds(), Any, datetime, Persist email to SQLite service_events table., Load Google OAuth credentials with multiple fallback search paths., Synchronous fetch executed in worker thread., Continuous background listener that monitors Gmail for new unread messages and…

### Community 69 - "ListRecentEmailsSkill"
Cohesion: 0.22
Nodes (9): ListRecentEmailsPipeline, Any, Pipeline that runs the ListRecentEmailsSkill. Demonstrates how higher‑level…, ListRecentEmailsSkill, List recent emails matching a query via Gmail API. Parameters ---------- query:…, asyncio, fixture, setup_skill() (+1 more)

### Community 70 - "poc.js"
Cohesion: 0.29
Nodes (9): clickSend(), isLoggedIn(), launchBrowser(), main(), path, PHONE, puppeteer, QR_SHOT (+1 more)

### Community 71 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 72 - "app/page.js"
Cohesion: 0.08
Nodes (36): AvatarStudioPage(), handleIntensityChange(), pollVolume(), runChoreography(), stopMotion(), triggerEmotion(), BASIC_VRM_EMOTIONS, CHARM_EMOTIONS (+28 more)

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

### Community 78 - "3. Control Deck Tabs & Capabilities"
Cohesion: 0.20
Nodes (9): 1. Directory Role & Boundary, 2. File Inventory, 3. Control Deck Tabs & Capabilities, 4. Critical Invariants & Gotchas, `app/avatar-studio/` — 3D Avatar Testing Studio, Tab 1: Gestures (43 Mocaps), Tab 2: Expressions & Visemes, Tab 3: Modes & States (+1 more)

### Community 79 - "skills.py"
Cohesion: 0.29
Nodes (7): list_skills(), Any, get, post, Return a list of registered skills (category == "skill")., Execute a skill by name with given parameters., run_skill()

### Community 80 - "tools.py"
Cohesion: 0.29
Nodes (7): list_tools(), Any, get, post, Return a list of registered tool names and descriptions., Execute a tool by name with given parameters., run_tool()

### Community 81 - "test_memory.py"
Cohesion: 0.12
Nodes (6): fake_agent_env(), FakeAdapter, mem_db_factory(), fixture, Tests for agent memory: short-term chat memory, long-term memory, and the…, Mock adapter that records calls and returns a fake plan or response.

### Community 82 - "system.py"
Cohesion: 0.22
Nodes (12): cancel_shutdown(), lock_workstation(), BaseModel, post, System control endpoints: Remote shutdown, restart, abort, and power management., Lock the Windows workstation immediately., Initiate a system shutdown with a safe countdown timer., Initiate a system restart with a countdown timer. (+4 more)

### Community 83 - "run_tunnel.py"
Cohesion: 0.71
Nodes (6): log(), main(), trigger_vercel_redeploy(), update_vercel_env(), wait_for_backend(), wait_for_network()

### Community 84 - "Read operations"
Cohesion: 0.25
Nodes (8): 8. File System Tools, `exists`, `list_directory`, `metadata`, Mutation operations, `read_file`, Read operations, `search_files`

### Community 86 - "TaskChainTracker.js"
Cohesion: 0.58
Nodes (8): formatResultString(), isDriveTool(), isEmailTool(), isWhatsAppTool(), isWorkerTool(), matchTools(), TaskChainTracker(), checkChainStatus()

### Community 87 - "🧠 JARVIS LIVING MEMORY & SYSTEM CONTEXT"
Cohesion: 0.25
Nodes (7): 💡 Active Preferences & Habits, 📁 Active Projects & Workspaces, 📜 Core Operational Rules (Manager Persona), 🧠 JARVIS LIVING MEMORY & SYSTEM CONTEXT, 📝 Recent Scratchpad (Rolling Active Notes), 📝 Scratchpad & Temporary Notes, 👤 User Profile & Invariants

### Community 88 - "OpenCodeAdapter"
Cohesion: 0.05
Nodes (31): _get_creds(), _load_token_path(), Any, Credentials, Path, Return a path to a ``token.json`` if one exists next to the tool or at the…, OpenCodeAdapter, Any (+23 more)

### Community 89 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 90 - "`app/workers/` — Worker Management & Launch Dashboard"
Cohesion: 0.22
Nodes (8): 1. Directory Role & Boundary, 2. File Inventory, 3. Core Features & Sub-components in `page.js`, 4. External API Contracts, 5. Critical Invariants & Gotchas, A. ForkForm (Worker Provisioning), `app/workers/` — Worker Management & Launch Dashboard, B. Worker Session Card Grid

### Community 91 - "lifecycle.py"
Cohesion: 0.15
Nodes (14): lifespan(), _periodic_memory_maintenance(), FastAPI, Periodic background task to aggregate daily digests and prune expired 7-day…, prewarm_vector_embedder(), Pre-warm the ONNX embedder model in a background thread at startup., DriveInboundListener, get_drive_listener() (+6 more)

### Community 93 - "layout.js"
Cohesion: 0.40
Nodes (3): geistMono, geistSans, metadata

### Community 95 - "`app/core/` — Core Engine, Tool Contracts & Reactive Orchestration"
Cohesion: 0.29
Nodes (6): 1. Directory Role & Boundary, 2. File Inventory, 3. Reactive Event Orchestrator (`app/core/events/`), 4. Universal Tool Contract (`BaseTool`), 5. Critical Invariants, `app/core/` — Core Engine, Tool Contracts & Reactive Orchestration

### Community 96 - "gmail/helpers/validation.py"
Cohesion: 0.40
Nodes (4): Validate that a search query string is non‑empty., Basic validation for an email address string. Returns True if the string looks…, validate_email_address(), validate_query()

### Community 97 - "AntigravityWorkerAgent"
Cohesion: 0.07
Nodes (36): Jarvis Central Brain Manager powered by Antigravity CLI (`agy.exe`). Features:…, _build_args(), _extract_session_id(), Any, Non-interactive Antigravity CLI client. Wraps `agy run` (or configured CLI) as…, Execute `agy` via stream-json stdin/stdout and collect structured results., Result of a single `agy run` invocation., Build the argument list for official Antigravity CLI (`agy.exe`). (+28 more)

### Community 98 - "Repository"
Cohesion: 0.12
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

### Community 108 - "Session: Worker / Orchestrator Architecture — Steps 0–1 (2026-09-12)"
Cohesion: 0.33
Nodes (6): Bug fixes along the way, Not yet done (next sessions), Session: Worker / Orchestrator Architecture — Steps 0–1 (2026-09-12), Step 0 — plumbing (done earlier same day), Step 1 — Word worker + worker LLM (this session), Verification

### Community 109 - "graphify.js"
Cohesion: 0.67
Nodes (3): graphAgeDays(), GraphifyPlugin(), IMPORTANT: keep the reminder string free of backticks and $(...) constructs.

### Community 110 - "7. Tool vs Skill vs Pipeline"
Cohesion: 0.50
Nodes (4): 7. Tool vs Skill vs Pipeline, Pipeline, Skill, Tool

### Community 113 - "list_pipelines"
Cohesion: 0.29
Nodes (7): list_pipelines(), Any, get, post, Return a list of available pipeline names., Execute a pipeline by name with given parameters., run_pipeline()

### Community 117 - "BaseTool"
Cohesion: 0.06
Nodes (49): ABC, BaseTool, Enum, str, Abstract base class for all filesystem tools. Subclasses must define ``name``,…, RiskLevel, Search Google Drive files by keyword, full-text content, and file type.…, SearchDriveSkill (+41 more)

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

### Community 137 - "EventType"
Cohesion: 0.15
Nodes (17): get_task_hooks(), HookRegistrationRequest, ManualEventRequest, publish_manual_event(), BaseModel, post, Return all registered/executed reactive task hooks., Register a reactive follow-up action to execute when target_session_id… (+9 more)

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

### Community 163 - "`app/api/` — HTTP & SSE API Gateway"
Cohesion: 0.33
Nodes (5): 1. Directory Role & Boundary, 2. Route Inventory (`app/api/routes/`), 3. Two-Phase Agent Architecture (`agent.py`), 4. Critical Invariants & Gotchas, `app/api/` — HTTP & SSE API Gateway

### Community 164 - "`app/lib/` — Networking & Shared Utilities"
Cohesion: 0.33
Nodes (5): 1. Directory Role & Boundary, 2. File Inventory, 3. Communication Contract, 4. Critical Invariants & Gotchas, `app/lib/` — Networking & Shared Utilities

### Community 166 - "verify_content"
Cohesion: 0.60
Nodes (5): Any, Path, verify_content(), verify_is_dir(), verify_is_file()

### Community 167 - "`app/modules/` — Domain Capabilities & Integrations"
Cohesion: 0.33
Nodes (5): 1. Directory Role & Boundary, 2. Module Inventory, 3. Module Internal Layout Convention, 4. Critical Invariants & Gotchas, `app/modules/` — Domain Capabilities & Integrations

### Community 168 - "Jarvis AI Automation — Backend Engine"
Cohesion: 0.33
Nodes (6): 1. Overview & Architecture, 2. Directory Map, 3. Environment Variables & Configuration, 4. Runbook & Common Commands, 5. Critical Invariants, Jarvis AI Automation — Backend Engine

### Community 169 - "WhatsAppInboundListener"
Cohesion: 0.16
Nodes (9): Any, Continuous background listener that monitors WhatsApp chats and emits digest…, Persist incoming chat preview to SQLite service_events table., Fetch and persist recent WhatsApp chats and messages into SQLite service_events…, WhatsAppInboundListener, asyncio, test_gmail_inbound_listener_emits_event(), test_whatsapp_inbound_listener_emits_event() (+1 more)

### Community 171 - "`tests/` — Backend Automated Test Suite"
Cohesion: 0.33
Nodes (5): 1. Directory Role & Boundary, 2. Test Suite Inventory (`tests/unit/`), 3. Running Tests, 4. Testing Conventions & Mocking, `tests/` — Backend Automated Test Suite

### Community 172 - "📋 Project Handover Brief"
Cohesion: 0.50
Nodes (3): 📂 Folder-Level Documentation, 📁 Key Files & Artifacts, 📋 Project Handover Brief

### Community 173 - "_load_token_path"
Cohesion: 0.25
Nodes (7): _get_creds(), _load_token_path(), Any, Credentials, Path, Load Gmail API credentials from token file or return None. Looks for…, Return credentials if present, otherwise respect ``GMAIL_MOCK``.

### Community 175 - "_get_shared_embedder"
Cohesion: 0.20
Nodes (6): _get_shared_embedder(), Any, Path, Try loading ONNX embedder singleton., Re-read JARVIS_MEMORY.md and rebuild the semantic index., Extract bullet points from memory sections (skipping invariants & profile).

### Community 176 - "workers.py"
Cohesion: 0.08
Nodes (37): _agent_factory_for(), factory(), approve_worker_plan(), ApprovePlanRequest, cancel_worker(), clear_all_workers(), _disk_sessions(), fork_worker() (+29 more)

### Community 177 - "main.py"
Cohesion: 0.18
Nodes (14): ExecutionError, jarvis_exception_handler(), JarvisException, NotFoundError, Request, create_app(), FastAPI, asyncio (+6 more)

### Community 178 - "FakeWhatsAppClient"
Cohesion: 0.12
Nodes (5): engine(), fake_client(), FakeWhatsAppClient, fixture, Records calls and returns canned sidecar responses.

### Community 180 - "base/bus.py"
Cohesion: 0.25
Nodes (8): emit_to_queues(), Any, Queue, Subscribe a new asyncio.Queue to receive live streaming events for session_id., Unsubscribe and remove an asyncio.Queue from session_id's active subscribers., Forward a streaming event to all active async queues subscribed to session_id…, subscribe(), unsubscribe()

### Community 181 - "tool_vector_index.py"
Cohesion: 0.28
Nodes (7): _build_index(), get_index(), Any, Semantic tool selector: FAISS index over tool example phrases. Loaded once at…, Encode all example phrases with ONNX embedder into a normalized NumPy matrix., Return or lazily initialize the global ONNX tool index matrix., Unit tests for FAISS vector tool selection.

### Community 182 - "Session: Optimizing the WhatsApp DOM Feature (2026-09-11)"
Cohesion: 0.33
Nodes (6): Context, Known limitations, Optimization plan (accepted next steps, not yet implemented), Root causes found & fixed (live debugging against real WhatsApp Web), Session: Optimizing the WhatsApp DOM Feature (2026-09-11), Verified live (through backend `:8000`, all ✅)

### Community 183 - "memory_vector_index.py"
Cohesion: 0.33
Nodes (4): Lazy-loaded MemoryVectorIndex for semantic on-demand retrieval., get_memory_vector_index(), Semantic memory retriever: Ultra-low latency ONNX + Keyword index over living…, Return the global MemoryVectorIndex instance.

### Community 185 - "core/config.py"
Cohesion: 0.29
Nodes (6): get_health(), HealthResponse, BaseModel, get, Settings, BaseSettings

### Community 195 - "organize_downloads_pipeline.py"
Cohesion: 0.33
Nodes (3): OrganizeDownloadsPipeline, Any, Pipeline that runs the OrganizeDownloadsSkill. It demonstrates how higher‑level…

### Community 198 - "ListDirectoryTool"
Cohesion: 0.21
Nodes (4): ListDirectoryTool, Any, Any, SearchContentTool

## Knowledge Gaps
- **429 isolated node(s):** `$schema`, `plugin`, `GESTURE_CATEGORIES`, `BASIC_VRM_EMOTIONS`, `EYE_WINK_CONTROLS` (+424 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1122 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Repository` connect `Repository` to `agent.py`, `GmailInboundListener`, `get_service_memory_manager`, `EventType`, `WhatsAppInboundListener`, `.build_brain_context_prompt`, `tasks.py`, `test_agent_fork.py`, `lifecycle.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `ExecutionEngine` connect `ExecutionEngine` to `agent.py`, `test_whatsapp.py`, `organize_downloads_pipeline.py`, `test_file_tools_v2.py`, `ListRecentEmailsSkill`, `TaskOrchestrator`, `execution_engine.py`, `EventType`, `skills.py`, `tools.py`, `main.py`, `WorkerEngine`, `test_tools_and_routes.py`, `test_search_content.py`, `BaseTool`, `FakeWhatsAppClient`, `ToolRegistry`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `WorkerSession` connect `WorkerSession` to `test_opencode_worker.py`, `TaskContract`, `get`, `TaskOrchestrator`, `EventType`, `worker_events`, `_contract`, `workers.py`, `main.py`, `WorkerEngine`, `test_session_handover.py`, `ToolRegistry`, `test_agent_fork.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `BaseTool` (e.g. with `ExecutionEngine` and `ToolRegistry`) actually correct?**
  _`BaseTool` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 48 inferred relationships involving `RiskLevel` (e.g. with `SearchDriveSkill` and `ListDriveFilesTool`) actually correct?**
  _`RiskLevel` has 48 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `WorkerSession` (e.g. with `approve_worker_plan()` and `clear_all_workers()`) actually correct?**
  _`WorkerSession` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `ExecutionEngine` (e.g. with `TaskOrchestrator` and `ExecutionError`) actually correct?**
  _`ExecutionEngine` has 26 INFERRED edges - model-reasoned connections that need verification._