# `app/` — FastAPI Application Shell & Lifespan

## 1. Directory Role & Boundary
The `app/` directory houses the core application initialization logic for the FastAPI server. It manages the lifespan lifecycle (startup checks, SQLite table provisioning, event loop integration), CORS middleware, and mounts all modular sub-routers.

---

## 2. File Inventory
| File | Role | Responsibilities |
| :--- | :--- | :--- |
| [`main.py`](file:///d:/AI-Automation/backend/app/main.py) | Application Factory | FastAPI app creation, CORS middleware setup, lifespan context manager, health checks, and router mounting. |
| [`__init__.py`](file:///d:/AI-Automation/backend/app/__init__.py) | Package Marker | Root package definition. |

---

## 3. Subdirectory Architecture
* [`api/`](file:///d:/AI-Automation/backend/app/api/README.md): REST endpoints and SSE streams.
* [`core/`](file:///d:/AI-Automation/backend/app/core/README.md): Engine abstractions (`BaseTool`, event bus, reactive orchestrator).
* [`modules/`](file:///d:/AI-Automation/backend/app/modules/README.md): Domain capabilities (Files, Gmail, Drive, Database, Memory, System).
* [`registry/`](file:///d:/AI-Automation/backend/app/registry/): Central catalog singleton (`registry`) where tools, skills, and pipelines register.
* [`workers/`](file:///d:/AI-Automation/backend/app/workers/README.md): Multi-job autonomous worker engines, sessions, and contracts.

---

## 4. Application Lifespan (`main.py`)
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    # 1. Initialize SQLite tables via SQLAlchemy (Base.metadata.create_all)
    # 2. Start reactive event orchestrator consumer loop
    yield
    # Shutdown:
    # Clean up event bus listeners & drain background tasks
```

---

## 5. Critical Invariants
* **Lazy Loading**: Domain adapters (such as `JarvisBrainManager` or `OpenCodeAdapter`) in route handlers must be loaded lazily inside dependency/helper functions (e.g. `_get_adapter()`). This prevents slow startup times or circular import deadlocks.
* **CORS Permissiveness**: During local development, CORS is configured to allow `http://localhost:3000` (Next.js frontend) and wildcard origins for tunneling.
