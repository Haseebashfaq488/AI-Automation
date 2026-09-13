Yes. Since **Phase 1 is already established**, we should now treat **Phase 2 as a focused backend engineering task**, not as “build Jarvis” all at once.

Your Phase 2 specification explicitly calls for the file-system module with `tools/`, `skills/`, `helpers/`, and `pipelines/`, covering file operations, search, validation/safety, and verification. 

Below is a **complete implementation context/prompt** you can give directly to another LLM/agent. It is intentionally detailed so the agent understands the architecture, boundaries, requirements, and definition of done.

---

# Phase 2 — Backend + File System Module

## 1. Project Context

We are building a local AI automation system called **Jarvis**.

The frontend is already established using **Next.js** and is intentionally simple. Do **not** redesign or rebuild the frontend during this phase.

Phase 1 has already established the basic backend/agent foundation:

* Remote requests can reach the local machine.
* The backend runs on the PC.
* The backend communicates with the remote frontend.
* OpenCode is integrated as the AI/operator layer.
* Basic agent/session state exists.
* The basic flow is:

```text
User
  ↓
Frontend
  ↓
Backend
  ↓
OpenCode / Agent
  ↓
Execution
  ↓
Response
```

Phase 2 now focuses on creating the **backend architecture and File System Module** that the agent can reliably use.

The important architectural principle is:

> **The LLM decides WHAT should happen. The backend tools determine HOW it happens.**

The LLM should not directly implement filesystem logic every time it wants to manipulate a file.

Instead:

```text
User request
     ↓
Agent reasoning
     ↓
Select tool / skill / pipeline
     ↓
Backend execution
     ↓
Filesystem
     ↓
Verification
     ↓
Structured result
     ↓
Agent
```

---

# 2. Primary Objective

Build a reliable Python backend foundation and implement the first real Jarvis capability:

> **A safe, observable, verifiable File System Module.**

The module must eventually allow the agent to perform requests such as:

```text
"Show me what's in my Downloads folder."

"Find all PDF files in my Downloads folder."

"Create a folder called invoices."

"Move all PDFs from Downloads into invoices."

"Rename this file."

"Read this text file."

"Create a new file."

"Delete this file."

"Organize my Downloads folder."

```

But the system must **not** accomplish this by allowing the LLM to arbitrarily execute shell commands.

Instead, the agent should use registered backend tools.

---

# 3. Technology Stack

Use the following stack unless there is a strong technical reason to change something.

## Backend

```text
Python 3.12+
FastAPI
Pydantic v2
SQLAlchemy 2.x
Alembic
SQLite
asyncio
httpx
pytest
Ruff
```

Use Python because this project will eventually involve:

* filesystem automation
* browser automation
* document processing
* system automation
* AI integrations
* local PC control

Keeping these capabilities primarily in Python avoids unnecessary cross-language complexity.

---

# 4. Backend Responsibilities

The backend should become the **control plane** of Jarvis.

It owns:

* API endpoints
* task creation
* task state
* tool registry
* skill registry
* pipeline registry
* execution
* validation
* verification
* logging
* execution history
* errors
* retries
* filesystem operations

OpenCode remains the AI/operator/reasoning layer.

Do **not** make OpenCode responsible for the underlying filesystem implementation.

---

# 5. High-Level Architecture

The target architecture should look approximately like this:

```text
                    ┌─────────────────────┐
                    │      Next.js        │
                    │      Frontend       │
                    └──────────┬──────────┘
                               │
                               │ HTTP / SSE
                               ↓
                    ┌─────────────────────┐
                    │      FastAPI        │
                    │       Backend      │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ↓                ↓                ↓
       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
       │ Task        │  │ Tool        │  │ Execution   │
       │ Manager     │  │ Registry    │  │ Engine      │
       └─────────────┘  └─────────────┘  └──────┬──────┘
                                                │
                         ┌──────────────────────┼─────────────────────┐
                         │                      │                     │
                         ↓                      ↓                     ↓
                  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
                  │ File System │       │ Future      │       │ Future      │
                  │ Module      │       │ Browser     │       │ System      │
                  └─────────────┘       │ Module      │       │ Module      │
                                        └─────────────┘       └─────────────┘

                               ↑
                               │
                        OpenCode / Agent
```

---

# 6. Project Structure

Create a clean modular structure.

Recommended:

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── tasks.py
│   │   │   └── tools.py
│   │   └── dependencies.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── exceptions.py
│   │   └── lifecycle.py
│   │
│   ├── agent/
│   │   ├── client.py
│   │   ├── session.py
│   │   └── adapter.py
│   │
│   ├── execution/
│   │   ├── engine.py
│   │   ├── context.py
│   │   ├── result.py
│   │   ├── errors.py
│   │   └── verification.py
│   │
│   ├── registry/
│   │   ├── tool_registry.py
│   │   ├── skill_registry.py
│   │   └── pipeline_registry.py
│   │
│   ├── tasks/
│   │   ├── manager.py
│   │   ├── models.py
│   │   └── states.py
│   │
│   ├── database/
│   │   ├── database.py
│   │   ├── models.py
│   │   └── migrations/
│   │
│   └── modules/
│       │
│       └── file_system/
│           │
│           ├── tools/
│           │   ├── read_file.py
│           │   ├── write_file.py
│           │   ├── create_folder.py
│           │   ├── delete.py
│           │   ├── move.py
│           │   ├── copy.py
│           │   ├── rename.py
│           │   ├── search.py
│           │   ├── list_directory.py
│           │   └── metadata.py
│           │
│           ├── skills/
│           │   ├── file_organization.py
│           │   ├── file_analysis.py
│           │   ├── document_processing.py
│           │   └── codebase_navigation.py
│           │
│           ├── pipelines/
│           │   ├── organize_downloads.py
│           │   ├── process_documents.py
│           │   └── backup_project.py
│           │
│           ├── helpers/
│           │   ├── paths.py
│           │   ├── validation.py
│           │   ├── permissions.py
│           │   └── verification.py
│           │
│           └── schemas.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── .env
├── .env.example
├── pyproject.toml
├── alembic.ini
└── README.md
```

Do not create unnecessary complexity beyond this.

The architecture must remain easy to understand.

---

# 7. Tool vs Skill vs Pipeline

This distinction is extremely important.

## Tool

A **tool** performs one atomic operation.

Example:

```text
read_file
move_file
rename_file
delete_file
search_files
create_folder
```

A tool should do one thing well.

---

## Skill

A **skill** combines tools to accomplish a reusable capability.

Example:

```text
organize_files
analyze_directory
analyze_codebase
process_documents
```

For example:

```text
file_organization skill

    search_files
        ↓
    analyze results
        ↓
    determine categories
        ↓
    move files
        ↓
    verify
```

---

## Pipeline

A **pipeline** is a predefined multi-step workflow.

Example:

```text
organize_downloads
```

could perform:

```text
inspect Downloads
       ↓
categorize files
       ↓
create folders
       ↓
move files
       ↓
verify results
       ↓
return summary
```

This distinction must be maintained throughout the project.

---

# 8. File System Tools

Implement the foundational tools first.

## Read operations

These should be low-risk.

### `list_directory`

Input:

```json
{
  "path": "~/Downloads"
}
```

Output:

```json
{
  "success": true,
  "path": "...",
  "entries": []
}
```

---

### `search_files`

Support:

* filename search
* extension filtering
* recursive search
* optional pattern matching

Example:

```json
{
  "path": "~/Downloads",
  "pattern": "*.pdf",
  "recursive": true
}
```

---

### `read_file`

Support text files initially.

Return structured information rather than raw uncontrolled output.

---

### `metadata`

Return information such as:

```text
name
path
size
extension
created_at
modified_at
is_file
is_directory
```

---

### `exists`

Determine whether a path exists.

---

## Mutation operations

Implement:

```text
create_file
write_file
create_folder
copy
move
rename
delete
```

These must go through centralized validation.

---

# 9. Path Safety

This is one of the most important requirements.

Do **not** allow every tool to independently manipulate arbitrary paths.

Create a centralized path layer.

For example:

```text
helpers/
    paths.py
    validation.py
```

Every filesystem operation should pass through this layer.

It should handle:

* path normalization
* absolute vs relative paths
* `~` expansion
* existence checks
* file/directory checks
* invalid path handling
* permission errors
* traversal concerns
* protected locations
* operation validation

Example conceptual flow:

```text
Agent says:

move_file(
    source="~/Downloads/a.pdf",
    destination="~/Documents/a.pdf"
)

        ↓

Path Resolver

        ↓

Path Validator

        ↓

Permission / Safety Check

        ↓

Filesystem Operation

        ↓

Verification

        ↓

Result
```

---

# 10. Risk Levels

Every tool should have a risk classification.

Example:

```text
LOW
    list_directory
    search_files
    read_file
    metadata
    exists

MEDIUM
    create_file
    write_file
    create_folder
    copy
    move
    rename

HIGH
    delete
    recursive delete
    overwrite
```

The execution engine should understand these levels.

This gives us the foundation for future permission policies.

---

# 11. Never Use Shell Commands for Normal File Operations

For ordinary filesystem operations, prefer Python APIs:

```text
pathlib
shutil
os
```

Do not implement:

```text
move → shell command
delete → shell command
mkdir → shell command
```

unless there is a genuine system-level reason.

The filesystem module should directly use Python.

This gives us:

* better error handling
* better portability
* easier testing
* structured exceptions
* better security
* easier verification

---

# 12. Structured Tool Contract

Every tool should follow a consistent interface.

Conceptually:

```python
Tool
├── name
├── description
├── input_schema
├── risk_level
├── execute()
└── verify()
```

A tool result should be structured.

Example:

```json
{
  "success": true,
  "tool": "move_file",
  "data": {
    "source": "...",
    "destination": "..."
  },
  "error": null,
  "metadata": {
    "duration_ms": 32
  }
}
```

Failure:

```json
{
  "success": false,
  "tool": "move_file",
  "data": null,
  "error": {
    "code": "DESTINATION_NOT_FOUND",
    "message": "Destination directory does not exist"
  }
}
```

Never make the LLM parse arbitrary exception strings if a structured error can be returned.

---

# 13. Verification

Every meaningful mutation should be followed by verification.

For example:

```text
move_file
   ↓
verify source no longer exists
   ↓
verify destination exists
```

For rename:

```text
rename
   ↓
verify old path doesn't exist
   ↓
verify new path exists
```

For create:

```text
create folder
   ↓
verify folder exists
```

For delete:

```text
delete
   ↓
verify target no longer exists
```

This is critical because Jarvis is eventually intended to be autonomous.

It should not blindly assume:

> "The operation probably worked."

It should know whether it worked.

---

# 14. Dry Run

Mutation tools should eventually support:

```json
{
  "dry_run": true
}
```

Example:

User:

```text
Organize my Downloads folder.
```

The system can first produce:

```text
Would create:
    Documents/
    Images/
    Videos/

Would move:
    report.pdf → Documents/
    photo.png → Images/
```

Then execute after approval/policy allows it.

Implement the underlying architecture for dry-run support even if the full UX is added later.

---

# 15. Idempotency

Tools should be designed so repeated execution is safe whenever possible.

Example:

If:

```text
create_folder("Documents")
```

is executed twice, the second operation should not unnecessarily fail.

Similarly, pipelines should avoid producing duplicate work.

This becomes very important when retry/recovery is introduced.

---

# 16. Execution Engine

Create a generic execution layer.

Conceptually:

```text
ExecutionEngine

execute(tool, parameters)

        ↓

validate input

        ↓

validate permissions

        ↓

execute tool

        ↓

capture result

        ↓

verify

        ↓

record execution

        ↓

return result
```

The execution engine should not contain filesystem-specific logic.

That logic belongs inside the File System Module.

This is important because Phase 3 and Phase 4 will reuse the same execution engine.

---

# 17. Tool Registry

Create a central registry.

Example:

```python
tool_registry.register(read_file)
tool_registry.register(write_file)
tool_registry.register(move_file)
tool_registry.register(search_files)
```

The agent should be able to ask:

```text
What tools are available?
```

and receive structured tool definitions.

Example:

```json
{
  "name": "move_file",
  "description": "Move a file or directory",
  "risk": "medium",
  "parameters": {
    "source": "string",
    "destination": "string"
  }
}
```

The registry must be independent of the filesystem implementation.

---

# 18. Skill Registry

Create the same concept for skills.

Example:

```text
file_organization
document_processing
codebase_navigation
file_analysis
```

The agent should be able to discover these.

---

# 19. Pipeline Registry

Same concept for pipelines.

Example:

```text
organize_downloads
process_documents
backup_project
```

The pipeline registry should expose:

```text
name
description
inputs
outputs
requirements
risk
steps
```

---

# 20. Pipeline Contract

Every pipeline should define:

```text
name
description
inputs
outputs
preconditions
steps
success_conditions
failure_conditions
recovery_strategy
```

Example:

```text
organize_downloads

Preconditions:
    Downloads exists

Steps:
    inspect directory
    categorize files
    create required directories
    move files
    verify moves

Success:
    files are located in expected categories

Failure:
    one or more operations failed

Recovery:
    report failed files
    do not silently continue destructive operations
```

---

# 21. Task Management

Introduce a task abstraction.

Example states:

```text
PENDING
RUNNING
WAITING
COMPLETED
FAILED
CANCELLED
```

Each task should have:

```text
task_id
created_at
started_at
completed_at
status
user_request
current_step
result
error
```

This gives the frontend something meaningful to display later.

---

# 22. Execution Journal

Record what happened.

For each task:

```text
Task
 ↓
Plan
 ↓
Tool call
 ↓
Parameters
 ↓
Result
 ↓
Verification
 ↓
Error/recovery
```

Example:

```text
Task: Organize Downloads

10:01:02  task_created
10:01:03  list_directory
10:01:03  result: 43 files
10:01:04  search_files *.pdf
10:01:04  result: 8 files
10:01:05  create_folder Documents
10:01:05  verified
10:01:06  move_file report.pdf
10:01:06  verified
```

Use SQLite initially.

Do not introduce Redis or a distributed queue yet.

---

# 23. Database

Use:

```text
SQLite
SQLAlchemy
Alembic
```

Initially store:

```text
tasks
task_events
execution_records
```

Potential structure:

```text
tasks
-----
id
status
request
created_at
started_at
completed_at
result
error

task_events
-----------
id
task_id
event_type
timestamp
payload

execution_records
-----------------
id
task_id
tool_name
parameters
result
success
duration
timestamp
```

Keep the schema simple.

The system currently runs on one PC, so PostgreSQL/Redis/distributed workers are unnecessary.

---

# 24. OpenCode Integration

OpenCode should not contain the actual filesystem implementation.

Instead create a thin adapter.

Conceptually:

```text
OpenCode
    ↓
Tool Adapter
    ↓
Backend Tool Registry
    ↓
Execution Engine
    ↓
File System Tool
```

For example, when OpenCode wants:

```text
move_file
```

it should invoke the backend's registered `move_file` capability.

The backend remains authoritative.

Do not duplicate filesystem logic inside OpenCode custom tools.

---

# 25. Agent Tool Interface

The agent should receive tools in a predictable format.

Example:

```json
{
  "name": "search_files",
  "description": "Search for files within a directory",
  "parameters": {
    "path": {
      "type": "string"
    },
    "pattern": {
      "type": "string"
    },
    "recursive": {
      "type": "boolean"
    }
  }
}
```

The LLM then produces something conceptually like:

```json
{
  "tool": "search_files",
  "parameters": {
    "path": "~/Downloads",
    "pattern": "*.pdf",
    "recursive": true
  }
}
```

The backend validates and executes it.

---

# 26. Error Handling

Create standardized errors.

Examples:

```text
PATH_NOT_FOUND
PERMISSION_DENIED
INVALID_PATH
FILE_NOT_FOUND
DIRECTORY_NOT_FOUND
ALREADY_EXISTS
INVALID_OPERATION
PROTECTED_PATH
OPERATION_FAILED
VERIFICATION_FAILED
TIMEOUT
```

The agent should receive:

```json
{
  "success": false,
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "...",
    "recoverable": true
  }
}
```

This allows the LLM to reason about failures.

---

# 27. Recovery

Do not implement a giant autonomous recovery system yet.

But design the interfaces so recovery can later work like:

```text
Tool fails
   ↓
Classify error
   ↓
Is it recoverable?
   ↓
Yes
   ↓
Agent diagnoses
   ↓
Retry / alternative tool / replan
```

Example:

```text
Destination doesn't exist

        ↓

Agent sees:
DESTINATION_NOT_FOUND

        ↓

Agent decides:

create_folder

        ↓

retry move_file

        ↓

verify
```

This is the foundation for Phase 5/7.

---

# 28. API Endpoints

Keep the initial API small.

At minimum:

```text
GET /health
```

```text
GET /tools
```

```text
GET /skills
```

```text
GET /pipelines
```

```text
POST /tasks
```

```text
GET /tasks/{task_id}
```

```text
GET /tasks/{task_id}/events
```

Potentially:

```text
POST /tools/{tool_name}/execute
```

for controlled internal/testing use.

Do not expose dangerous arbitrary filesystem functionality directly through unauthenticated public endpoints.

---

# 29. Frontend Integration

The frontend is already established.

Do not redesign it.

Only provide the backend contracts it needs.

The frontend should eventually be able to:

```text
submit task
      ↓
receive task ID
      ↓
observe task status
      ↓
observe execution events
      ↓
display result
```

Initially:

```text
REST → commands
SSE → live execution events
```

WebSockets are not required yet unless the existing frontend architecture already depends on them.

---

# 30. Configuration

Use environment variables.

Create:

```text
.env
.env.example
```

Configuration should include things such as:

```text
APP_ENV
BACKEND_HOST
BACKEND_PORT
DATABASE_URL
LOG_LEVEL
OPENCODE_URL
```

Do not hardcode machine-specific paths.

---

# 31. Logging

Use structured logging.

Every important event should include things such as:

```text
timestamp
task_id
tool
operation
duration
success
error
```

Example:

```text
task_id=abc123
tool=move_file
success=true
duration_ms=42
```

Avoid logging sensitive file contents unnecessarily.

---

# 32. Testing

Testing is mandatory.

Create tests for:

### Unit tests

```text
path resolution
path validation
file existence
directory listing
search
read
write
create
move
copy
rename
delete
verification
```

### Integration tests

Test workflows such as:

```text
create folder
   ↓
create file
   ↓
move file
   ↓
rename file
   ↓
verify
```

Use temporary directories.

**Never run destructive tests against the user's actual filesystem.**

---

# 33. Safety Requirements

The system is intended to eventually have very powerful PC access.

Therefore:

### Never

Allow the LLM to silently execute arbitrary:

```text
shell commands
PowerShell
cmd
Python code
```

for ordinary filesystem tasks.

### Instead

Use explicit registered capabilities:

```text
read_file
write_file
move_file
delete_file
...
```

This gives us control and observability.

---

# 34. Protected Paths

Design support for protected paths.

Eventually the system should be able to prevent dangerous operations against locations such as:

```text
Windows system directories
Program Files
critical application directories
backend source directory
database directory
```

The exact protected-path policy can evolve.

For now, implement the abstraction rather than hardcoding an enormous list.

---

# 35. Important Architectural Rule

Do not build this:

```text
LLM
 ↓
generate Python code
 ↓
execute Python code
 ↓
hope it works
```

Build this:

```text
LLM
 ↓
choose capability
 ↓
structured parameters
 ↓
backend validates
 ↓
backend executes
 ↓
backend verifies
 ↓
structured result
 ↓
LLM
```

This distinction is fundamental to the project.

---

# 36. Development Order

Do the implementation in this exact order.

## Step 1 — Backend foundation

Set up:

```text
Python
FastAPI
Pydantic
SQLAlchemy
Alembic
SQLite
pytest
Ruff
```

Make:

```text
GET /health
```

work.

---

## Step 2 — Core architecture

Implement:

```text
config
logging
exceptions
task model
execution result
execution context
```

---

## Step 3 — Tool system

Implement:

```text
Tool interface
ToolResult
ToolRegistry
ExecutionEngine
```

Test the registry independently.

---

## Step 4 — File System helpers

Implement:

```text
path resolver
path validator
permission checks
verification helpers
```

Test these heavily.

---

## Step 5 — Read-only filesystem tools

Implement:

```text
exists
metadata
list_directory
search_files
read_file
```

Test everything using temporary directories.

---

## Step 6 — Mutation tools

Implement:

```text
create_file
write_file
create_folder
copy
move
rename
delete
```

Add:

```text
risk levels
dry run
validation
verification
structured errors
```

---

## Step 7 — Task execution

Connect:

```text
Task Manager
    ↓
Execution Engine
    ↓
Tool Registry
    ↓
Filesystem
```

Record execution events in SQLite.

---

## Step 8 — OpenCode integration

Connect OpenCode to the backend tool system.

Do not duplicate tool logic.

---

## Step 9 — Skills

Implement:

```text
file_organization
file_analysis
codebase_navigation
document_processing
```

Only build useful functionality; don't over-engineer them.

---

## Step 10 — Pipelines

Implement at least:

```text
organize_downloads
```

and one additional useful pipeline.

Every pipeline must include:

```text
preconditions
steps
success conditions
failure conditions
verification
```

---

## Step 11 — API exposure

Expose:

```text
/tools
/skills
/pipelines
/tasks
/tasks/{id}
/tasks/{id}/events
```

---

## Step 12 — End-to-end test

The final test should resemble:

```text
User:

"Create a folder called test inside my Downloads folder,
create a text file inside it, write some text to the file,
then rename the file."

        ↓

Frontend

        ↓

Backend

        ↓

OpenCode

        ↓

Tool selection

        ↓

create_folder

        ↓

create_file

        ↓

write_file

        ↓

rename

        ↓

verification

        ↓

execution journal

        ↓

final response
```

---

# 37. Definition of Done

Phase 2 is **not complete** merely because the backend starts.

Phase 2 is complete when the system can reliably perform requests like:

```text
List my Downloads folder.

Find all PDFs in Downloads.

Read this text file.

Create a folder.

Create a file.

Write to a file.

Move a file.

Copy a file.

Rename a file.

Delete a file.

Organize a directory.
```

through the proper architecture:

```text
LLM
 ↓
Tool / Skill / Pipeline
 ↓
Registry
 ↓
Execution Engine
 ↓
Validation
 ↓
Filesystem
 ↓
Verification
 ↓
Execution Journal
 ↓
Result
```

And the following are true:

* filesystem tools are independently testable
* paths are validated centrally
* destructive operations have risk levels
* mutations are verified
* errors are structured
* tasks are persisted
* execution is logged
* tools are discoverable
* OpenCode uses the backend capabilities rather than duplicating them
* frontend does not need filesystem-specific logic
* architecture can support Browser and System modules later

---

# 38. What NOT to Build Yet

Do **not** expand Phase 2 into the entire Jarvis system.

Do not build yet:

```text
browser automation
Chrome control
system automation
multi-agent swarm
specialized AI workers
self-healing code modification
long-term memory
scheduling
voice interface
complex distributed queues
Redis
Kubernetes
microservices
```

Those belong to later phases.

The goal right now is:

> **Build a rock-solid backend execution foundation and File System Module that every future Jarvis capability can build upon.**

The same architecture will later be reused:

```text
file_system/
browser/
system/
research/
documents/
...
```

with:

```text
tools/
skills/
helpers/
pipelines/
```

as specified in the overall project plan. 

---

# 39. Instructions to the Implementing LLM

Give the implementation agent these operating rules:

```text
You are implementing Phase 2 of the Jarvis project.

Do not redesign the architecture unless there is a concrete technical reason.

Before changing existing code:
1. Inspect the existing backend.
2. Understand the current Phase 1 implementation.
3. Identify existing APIs, agent integration, configuration, and project structure.
4. Reuse existing functionality where appropriate.
5. Do not duplicate existing functionality.

Implement Phase 2 incrementally.

After each major component:
1. Run tests.
2. Run type/lint checks.
3. Start the backend.
4. Verify the relevant API.
5. Fix errors before moving forward.

Do not silently skip requirements.

Do not replace working architecture merely because another approach is personally preferred.

Do not build future phases prematurely.

Keep filesystem implementation separate from the agent.

The LLM chooses WHAT to do.
The backend determines HOW to execute it.

Never give the LLM unrestricted filesystem or shell access when a registered backend tool can perform the operation.

Every mutation must be validated and verified.

Every important execution must be observable through structured logs/events.

Use temporary directories for filesystem tests.

Never use the user's real filesystem as a destructive test environment.

When uncertain about existing project behavior, inspect the code first instead of assuming.

At the end of each implementation milestone:
- summarize what changed
- list files changed
- list tests executed
- report any remaining issues
- do not claim success if something was not actually tested.
```

---

## The actual Phase 2 target

If I were directing the implementation, I'd keep the mental model extremely simple:

```text
                    JARVIS BACKEND
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
       Tools          Skills        Pipelines
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                 Execution Engine
                         ↓
              Validation + Safety
                         ↓
                  Real Computer
                         ↓
                    Verification
                         ↓
                 Execution Journal
                         ↓
                    Agent Result
```

**That is the foundation we want to get right now.** Once this works reliably, Browser, System Control, and the later Pipeline Orchestrator can plug into the same architecture rather than requiring a rewrite. Your original phase plan explicitly intends the later modules to follow this progression. 

If you paste the context above into your implementation LLM, the **first instruction should be: inspect the existing Phase 1 backend before writing any code**. That prevents it from accidentally rebuilding pieces you already have.
