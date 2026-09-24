# Jarvis AI Automation — Backend Engine

## 1. Overview & Architecture
The Jarvis Backend is a high-performance Python 3.13 / FastAPI asynchronous engine that serves as the executive brain, task coordinator, and autonomous worker orchestrator for personal automation.

```
Frontend (Next.js 16)   :3000   AI-Automation Frontend/   (Repo: Haseebashfaq488/Ai-Automation-Frontend)
        │
        ▼ REST / SSE
Backend  (FastAPI)      :8000   backend/                  (Repo: Haseebashfaq488/AI-Automation)
        ├── Antigravity Brain   (Gemini 3.8 Flash multi-turn executive agent)
        ├── Event Orchestrator  (Reactive downstream task chains)
        ├── Tool Registry       (File management, Gmail, Google Drive, System)
        └── Worker Sessions     (Multi-job autonomous background workers)
```

---

## 2. Directory Map
| Directory | Living Documentation | Focus |
| :--- | :--- | :--- |
| **`app/`** | [`app/README.md`](file:///d:/AI-Automation/backend/app/README.md) | FastAPI app factory (`main.py`), CORS configuration, and lifespan initialization. |
| **`app/api/`** | [`app/api/README.md`](file:///d:/AI-Automation/backend/app/api/README.md) | REST & SSE API gateway (`/agent`, `/workers`, `/events`, `/tasks`, `/system`). |
| **`app/core/`** | [`app/core/README.md`](file:///d:/AI-Automation/backend/app/core/README.md) | Base tool contracts, in-memory event bus, and reactive event orchestrator. |
| **`app/modules/`** | [`app/modules/README.md`](file:///d:/AI-Automation/backend/app/modules/README.md) | Domain plugins (Google Drive, Gmail, SQLite Database, Living Memory, Files). |
| **`app/workers/`** | [`app/workers/README.md`](file:///d:/AI-Automation/backend/app/workers/README.md) | 3-job autonomous worker engine, living docs scanner, and graphify handover synthesis. |
| **`tests/`** | [`tests/README.md`](file:///d:/AI-Automation/backend/tests/README.md) | Pytest test suites, fixture patterns, and mock configurations. |

---

## 3. Environment Variables & Configuration
Configure via `backend/.env` (see `.env.example`):

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `JARVIS_WORKSPACE` | Default fallback filesystem scope for workers & file operations | `D:/workspace` |
| `GEMINI_API_KEY` | Google Gemini API key for Antigravity Brain | `AIzaSy...` |
| `GROQ_API_KEY` | Groq API key (fallback LLM planning engine) | `gsk_...` |
| `DATABASE_URL` | SQLite database connection string | `sqlite:///./jarvis.db` |
| `GMAIL_MOCK` | Set to `1` to return mock emails without live Google OAuth | `0` |
| `DRIVE_MOCK` | Set to `1` to return mock Drive files without live Google OAuth | `0` |

---

## 4. Runbook & Common Commands

```powershell
# 1. Start the FastAPI backend server (from backend/)
uvicorn app.main:app --port 8000 --reload

# 2. Run unit tests
pytest tests/unit/

# 3. Google OAuth Setup (if tokens expired)
python setup_gmail_oauth.py     # Refreshes backend/token.json (Gmail scopes)
python setup_drive_oauth.py     # Refreshes backend/drive_token.json (Drive scopes)

# 4. AST Knowledge Graph Sync (from project root)
graphify update .
```

---

## 5. Critical Invariants
* **OAuth Token Path**: Never store OAuth tokens anywhere except `backend/token.json` (Gmail) and `backend/drive_token.json` (Drive). The tools and skills only inspect these canonical paths.
* **Console Encoding**: Always ensure UTF-8 encoding when printing emojis or logs on Windows: `$env:PYTHONIOENCODING = "utf-8"`.
* **Workspace Scoping**: Tools and worker contracts must resolve targets dynamically from user requests, falling back to `JARVIS_WORKSPACE`.
