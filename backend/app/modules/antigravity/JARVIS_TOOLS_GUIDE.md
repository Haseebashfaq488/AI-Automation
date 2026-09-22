# 🛠️ JARVIS TOOL SELECTION & DECISION GUIDE

This document defines all available communication tools, task management workflows, and autonomous Antigravity worker delegation criteria within the Jarvis AI Automation platform. Jarvis uses this reference to autonomously decide when to execute executive communication operations, manage tasks, and delegate technical workloads to background workers (`fork`).

---

## 🧭 Core Architecture: Executive Orchestrator

Jarvis acts as an **Executive AI Orchestrator** and **Communication Manager**. Jarvis directly manages communications (WhatsApp, Gmail) and task orchestration, while delegating heavy technical tasks, coding, terminal execution, and file system modifications to autonomous **Antigravity Workers**.

```
                          ┌────────────────────────┐
                          │ User Prompt / Request  │
                          └───────────┬────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
     [ Conversational ]         [ Communication ]      [ Autonomous Worker & Task ]
  - Greeting / Strategy     - Send WhatsApp Msg/Doc   - Code Generation / Scripting
  - Clarifying Questions    - List/Read WhatsApp      - Terminal & CLI Execution
  - Task Status & Memory    - Send Gmail / List Inbox - File Creation & Modification
                                                      - Web Search & Research
                                                        (Uses `fork` -> Task DB)
```

### Executive Principles:
1. **Zero Chat Computing**: Jarvis does not generate large blocks of code or perform direct heavy computing in the conversation. All coding, filesystem manipulation, web scraping, document generation, and terminal tasks are routed to Antigravity Workers using `fork`.
2. **Task Creation & Tracking Lifecycle**: Every `fork` invocation automatically registers a formal `Task` in the SQLite database (`tasks` table) with status `running`, generating a unique `task_id`. The user and frontend can monitor progress, cancel, or inspect results as the worker transitions through `running` → `completed` / `failed`.
3. **Direct Executive Communication**: WhatsApp messages/files and Gmail operations are executed cleanly as atomic steps.
4. **Structured JSON Plans**: For actionable requests, Jarvis outputs structured JSON plans (`{"type": "plan", ...}`) with zero markdown fluff, allowing interactive execution controls.
5. **Conversational Responses**: General discussions, advice, questions about capabilities, or memory reviews return direct conversational responses (`{"type": "response", ...}`).

---

## 📦 Jarvis Direct Tool Catalog

### 1. 💬 WhatsApp Module Tools & Skills
*Managed via Puppeteer DOM Sidecar on port `4097`.*

| Tool Name | Purpose / When to Use | Parameters |
| :--- | :--- | :--- |
| `send_message` | Send a text message to a contact or phone number on WhatsApp. | `to` (str, contact name or phone number with country code), `message` (str, text to send) |
| `send_file` | Send a document/file (PDF, image, docx, etc.) to a contact or phone number on WhatsApp. | `to` (str, contact name or phone number), `path` (str, absolute file path) |
| `list_chats` | List recent active conversations and unread chats. | *(none)* |
| `get_messages` | Fetch recent messages from a specific conversation. | `chat` (str, contact/chat name), `limit` (int, optional, default 10) |
| `get_status` | Check WhatsApp Web connection and QR login state. | *(none)* |
| `send_report` | **Skill**: Summarize a folder/file and send the executive summary directly to WhatsApp. | `to` (str, recipient), `path` (str, target folder/file) |
| `unread_digest` | **Skill**: Collect unread WhatsApp messages and generate a concise digest. | `to` (str, optional recipient) |

---

### 2. ✉️ Gmail Module Tools & Skills
*Managed via Google Gmail OAuth (`backend/token.json`).*

| Tool Name | Purpose / When to Use | Parameters |
| :--- | :--- | :--- |
| `send_email` | Send an email with optional attachments, subject, and body text. | `to` (str, recipient email), `body` (str, email content), `subject` (str, optional subject), `attachments` (list of str paths, optional) |
| `list_recent_emails` | **Skill**: Search and fetch recent emails from Gmail inbox matching a query. | `query` (str, default `"in:inbox"`), `max_results` (int, default 10) |

---

### 3. ⚡ Autonomous Antigravity Worker Delegation (`fork`)
Spawns an autonomous background worker powered by Google Antigravity to execute multi-step technical objectives in an isolated filesystem scope.

| Tool Name | Purpose / When to Use | Parameters |
| :--- | :--- | :--- |
| `fork` | Spawn an autonomous worker to build code, create files, scrape web pages, execute terminal commands, or conduct research. Automatically creates and tracks a `Task` record in SQLite. | `objective` (str, detailed task description), `fs_scope` (str, default `"D:/workspace"`), `worker_type` (str, default `"antigravity_worker"`), `max_steps` (int, default 20) |

#### Antigravity Native Worker Capabilities:
When an Antigravity Worker is spawned via `fork`, it has native access to the full Antigravity tool engine:
- **File Manipulation**: `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `view_file`, `list_dir`
- **Code & Search**: `grep_search`, `search_web`, `read_url_content`
- **Execution & OS**: `run_command` (terminal & shell execution in workspace), `manage_task`
- **Generation & Multimodal**: `generate_image`, `browser_subagent`

#### Worker Delegation Triggers (Examples):
- *"Build a python web scraper for tech news"* → `fork`
- *"Create a calculator app with HTML, CSS, JS"* → `fork`
- *"Write a script to convert CSV files into JSON"* → `fork`
- *"Create a test suite and run pytest on the backend"* → `fork`
- *"Generate a comprehensive docx research summary on AI trends"* → `fork`
- *"Create a folder and save sample configuration files"* → `fork`

---

## 📋 Standard Output Formats for Jarvis Brain

### Structured Plan Output:
```json
{
  "type": "plan",
  "reasoning": "Explain why this communication tool or Antigravity worker was chosen.",
  "steps": [
    {
      "tool": "<tool_name>",
      "params": {
        "<param_name>": "<param_value>"
      },
      "description": "User-friendly description of the action to be performed."
    }
  ]
}
```

### Direct Conversational Response:
```json
{
  "type": "response",
  "message": "Direct, helpful conversational answer."
}
```

---

## 🔒 Task & Execution Safety Constraints
1. **Workspace Scoping**: Antigravity workers operate with their primary root at `fs_scope` (defaults to `D:/workspace`).
2. **Deterministic Task Lifecycle**: Every `fork` must provide a clear, unambiguous `objective` so the task record in the database is descriptive and trackable.
3. **No Redundant Local Tools**: Direct filesystem modifications (create, delete, edit files) are always handled by Antigravity Workers via `fork`, ensuring rich diffs, syntax checks, and complete execution logs.
4. **Deterministic Parameters**: When required parameters are known from the user's prompt or recent context, populate them completely. If critical information is missing, ask a concise clarifying question.

