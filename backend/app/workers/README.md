# `app/workers/` — Autonomous Background Worker Engine

## 1. Directory Role & Boundary
The `app/workers/` directory implements the autonomous background worker execution runtime. It isolates long-running coding, refactoring, and engineering tasks from the main FastAPI server process, enforcing strict filesystem boundaries, 3-job milestones, and automated session handover synthesis.

---

## 2. Directory Layout & Components
| Subdirectory / File | Role | Key Responsibilities |
| :--- | :--- | :--- |
| **`base/engine.py`** | Engine Controller | `WorkerEngine`: Runs the autonomous lifecycle, drives the 3 milestone jobs, manages safety timeouts, and orchestrates finalization. |
| **`base/contract.py`** | Contract Specification | `TaskContract`: Immutable task spec containing `objective`, `requirements`, `constraints`, `fs_scope`, `prior_handover`, `is_refinement`, and `has_graphify`. |
| **`base/session.py`** | Session Persistence | `WorkerSession`: Manages disk storage in `backend/worker_sessions/{session_id}/` (`events.jsonl`, `task.json`, `result.json`, `handover.json`, `SESSION_HANDOVER.md`, `artifacts/`). |
| **`base/bus.py`** | Session Bus | Pub/sub channel for streaming step updates and lifecycle events to connected SSE clients. |
| **`base/guardian.py`** | Output Guardian | Real-time terminal output safety filter preventing data leakage or corrupted streaming buffers. |
| **`antigravity_worker/`** | Antigravity Runtime | Worker implementation powered by the Antigravity binary CLI and Gemini 3.8 Flash. Multi-job milestone prompts (`milestones.py`) and streaming CLI client (`cli_client.py`). |
| **`opencode_worker/`** | OpenCode Runtime | Lightweight tool-loop fallback worker. |

---

## 3. The 3-Job Milestone Protocol
Every autonomous Antigravity worker executes through 3 distinct jobs:

```
┌────────────────────────────────────────────────────────┐
│ Job 1: Implementation Planning & Review                │
│ -> Worker analyzes requirements & inspects codebase    │
│ -> Emits plan.md -> Status: awaiting_plan_approval    │
│ -> (Human operator approves or provides revision)      │
└──────────────────────────┬─────────────────────────────┘
                           │ Plan Approved
┌──────────────────────────▼─────────────────────────────┐
│ Job 2: Plan Execution & Delta Implementation           │
│ -> Worker executes plan steps with tool loop           │
│ -> Creates/modifies code, updates subfolder READMEs   │
└──────────────────────────┬─────────────────────────────┘
                           │ Execution Done
┌──────────────────────────▼─────────────────────────────┐
│ Job 3: Self-Testing & Verification Gate                │
│ -> Worker generates & runs automated unit test suite   │
│ -> Emits test-results.json (pass rate, exit codes)     │
└──────────────────────────┬─────────────────────────────┘
                           │ Tests Complete
┌──────────────────────────▼─────────────────────────────┐
│ Finalize: Living Docs & Graphify Handover Synthesis    │
│ -> Scans all touched subfolders for README.md manifests│
│ -> Runs 'graphify update .' to rebuild AST graph       │
│ -> Emits SESSION_HANDOVER.md & handover.json           │
└────────────────────────────────────────────────────────┘
```

---

## 4. Finalization & Handover Synthesis (`_synthesize_handover`)
When a worker completes Job 3, `WorkerEngine._finalize()` automatically:
1. **Scans Subfolder Living Docs**: Traverses the worker's `fs_scope` to collect all `README.md` manifests created or updated by the worker.
2. **Executes Graphify**: Runs `graphify update .` (or `graphify extract . --code-only`) in the workspace, generating or updating `graphify-out/`.
3. **Generates Root Handover**:
   * Writes `SESSION_HANDOVER.md` and `handover.json` both in the session directory and the workspace root.
   * Records completed objectives, architectural decisions, modified files, test pass rates, and next-worker guidance.

---

## 5. Non-Destructive Refinement Protocol
When a new worker is launched in a directory that already contains a `SESSION_HANDOVER.md`:
* The backend automatically flags `is_refinement = True` and loads `prior_handover`.
* The worker prompt is injected with the prior architecture, living doc manifests, and AST graph query instructions (`graphify query`, `graphify path`).
* The worker is strictly instructed to apply incremental delta updates and maintain existing tests without clobbering prior work.

---

## 6. Critical Invariants & Gotchas

| Gotcha / Failure Mode | Root Cause | Preventative Guardrail |
| :--- | :--- | :--- |
| **Worker hangs in Job 3 during test suite execution** | Integration test executed `subprocess.run()` without `timeout`, and target script launched a blocking Tkinter/Qt event loop (`root.mainloop()`) or blocking stdin prompt. | `milestones.py` enforces mandatory `timeout=10` on all child subprocesses, and explicitly prohibits invoking blocking UI event loops or interactive terminal prompts inside test suites. |
| **Silent CLI timeout (1800s)** | `agy` CLI milestone timeout defaults to 30 min (`ANTIGRAVITY_TIMEOUT=1800`). If a test hangs, the engine remains in `running` status until timeout expires. | Strict subprocess timeouts in test assertions ensure child scripts fail fast (`TimeoutExpired`) instead of freezing the CLI runner. |
| **Non-interactive / Headless testing for dual CLI/GUI apps** | Automated tests invoking dual CLI/GUI entrypoints default to GUI when no args are passed. | Tests must pass `--cli`, `--non-interactive`, or instantiate widgets headlessly (`root.update(); root.destroy()`). |

