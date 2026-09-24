# `app/modules/` — Domain Capabilities & Integrations

## 1. Directory Role & Boundary
The `app/modules/` directory contains all domain-specific plugins, integrations, and operational tools for Jarvis. Each module is self-contained with its own tools, skills, helpers, and tests.

---

## 2. Module Inventory
| Module | Role | Key Tools / Responsibilities |
| :--- | :--- | :--- |
| **`antigravity`** | Executive Brain | `JarvisBrainManager` (`brain.py`), tool vector semantic index (`tool_vector_index.py`), long-term fact extraction, and memory files (`JARVIS_MEMORY.md`). |
| **`database`** | SQLite Persistence | SQLAlchemy session management (`db.py`), ORM models (`models.py`: `Task`, `Memory`, `AuditLog`), and Repository CRUD layer (`repository.py`). |
| **`memory`** | Context Memory | `ChatMemory` (20-message short-term sliding window), `LongTermMemory` (deduplicated persistent facts in SQLite), and `ServiceMemory`. |
| **`drive`** | Google Drive | `list_drive_files`, `read_drive_file`, `upload_drive_file`, `search_drive` (skill). Supports OAuth auto-refresh and mock mode (`DRIVE_MOCK=1`). |
| **`gmail`** | Gmail Integration | `send_email` (with attachment support up to 25MB), `list_recent_emails` (skill), auto-refresh OAuth client (`backend/token.json`), and mock mode (`GMAIL_MOCK=1`). |
| **`file_management`**| Filesystem Operations | 11 safety-checked file tools: `list_directory`, `read_file`, `write_file`, `create_file`, `create_folder`, `delete_file` (to trash), `archive_folder`, `extract_archive`. |
| **`system`** | System Controls | Hardware telemetry (CPU, RAM, Battery) and power management actions (`system_lock`, `system_sleep`). |
| **`opencode`** | LLM Fallback | `OpenCodeAdapter`: Fallback planning adapter using Groq LLM when Antigravity CLI binary is unavailable. |
| **`whatsapp`** | WhatsApp Web | *Historical DOM automation module (Retained for reference; deferred in favor of direct APIs).* |

---

## 3. Module Internal Layout Convention
To add a new capability, follow the standard module layout:
```
app/modules/<module_name>/
├── __init__.py
├── helpers/       # Internal SDK wrappers, OAuth clients, or serializers
├── tools/         # Individual BaseTool implementations
├── skills/        # Multi-tool composite skills
└── pipelines/     # Automated event-driven workflows
```

---

## 4. Critical Invariants & Gotchas
* **OAuth Token Placement**:
  * Gmail token: **`backend/token.json`**
  * Drive token: **`backend/drive_token.json`**
  * Do NOT save tokens in arbitrary subdirectories. The OAuth helpers only load and refresh from these canonical locations.
* **Mock Mode for Demos & Tests**: Setting `GMAIL_MOCK=1` or `DRIVE_MOCK=1` bypasses live Google APIs and returns realistic structured fixtures. Unit tests monkeypatch token loaders to run independently of real credentials.
* **Planning Prompt Alignment**: When adding new tools, register them in `app/registry/` and ensure their signatures are reflected in `app/modules/antigravity/brain.py` and `app/modules/opencode/adapter.py`.
