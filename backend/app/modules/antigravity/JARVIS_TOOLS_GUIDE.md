# 🛠️ JARVIS TOOL SELECTION & DECISION GUIDE

This document defines all available tools, skills, pipelines, and autonomous worker delegation criteria within the Jarvis AI Automation platform. Jarvis uses this reference to autonomously decide when to execute atomic operations, when to delegate to background workers (`fork`), and how to format tool execution plans.

---

## 🧭 Core Decision Architecture

Jarvis operates on a 3-tier action hierarchy:

```
                          ┌────────────────────────┐
                          │ User Prompt / Request  │
                          └───────────┬────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
     [ Conversational ]         [ Atomic Tool ]      [ Autonomous Worker ]
  - Greeting / Identity     - Direct File Op       - Multi-step Coding
  - System Capabilities     - Send WhatsApp/Email  - Web Scraping Script
  - Memory Read / Scratch   - List Directory       - Document Generation
                            - Search / Metadata    - Refactor / Test Suite
                                                     (Uses `fork` tool)
```

### Decision Rules:
1. **Manager & Orchestrator Role**: Jarvis does not generate code directly into the chat response. For any generative or multi-step technical request (e.g. "create a script", "build an app", "scrape data", "generate docx"), Jarvis creates a plan with the `fork` tool targeting `D:/workspace`.
2. **Direct Atomic Operations**: When the user requests an explicit single-step operation (e.g. read a file, send a WhatsApp message, send an email, search files, list a directory), Jarvis returns a plan with that exact atomic tool and its extracted parameters.
3. **No Asking Permission in Chat**: Jarvis returns structured JSON plans directly (`{"type": "plan", ...}`) so the interactive user interface can render confirmation and execution controls.
4. **Conversational Responses**: Questions about capabilities, identity, greetings, or memory review return a conversational response (`{"type": "response", ...}`).

---

## 📦 Complete Tool Catalog

### 1. 📁 File Management Tools (Atomic & Safe)

| Tool Name | Purpose / When to Use | Required Parameters | Optional Parameters |
| :--- | :--- | :--- | :--- |
| `list_directory` | List files and subfolders in a folder. Use when user asks "what files are in folder X", "ls", "show directory". | `path` (str, absolute path) | `recursive` (bool) |
| `exists` | Check if a file or directory exists on disk. Use for existence verification queries. | `path` (str, absolute path) | - |
| `metadata` | Get file details: size in bytes, creation time, modification time, permissions, is_dir. | `path` (str, absolute path) | - |
| `search_files` | Search for files by filename matching a glob pattern (e.g. `*.pdf`, `test_*.py`). | `path` (str, search root), `pattern` (str, glob) | `recursive` (bool) |
| `search_content` | Search for text/keywords inside files (grep-like). Use when looking for content inside files. | `path` (str, file or directory), `query` (str) | `case_sensitive` (bool), `max_results` (int) |
| `read_file` | Read the text contents of a file (UTF-8). Truncates safely for large files. | `path` (str, absolute path) | - |
| `create_file` | Create a new file with initial content (or empty). | `path` (str, absolute path) | `content` (str) |
| `create_folder` | Create a new directory. Recursively creates parents if needed. | `path` (str, absolute path) | - |
| `write_file` | Overwrite or write content to a file. | `path` (str, absolute path), `content` (str) | - |
| `append_file` | Append text content to an existing file. | `path` (str, absolute path), `content` (str) | - |
| `touch` | Create an empty file or update the last modified timestamp. | `path` (str, absolute path) | - |
| `copy` | Copy a file or directory from source to destination. | `source` (str, absolute path), `destination` (str, absolute path) | - |
| `move` | Move/relocate a file or folder from source to destination. | `source` (str, absolute path), `destination` (str, absolute path) | - |
| `rename` | Rename a file or folder. | `source` (str, absolute path), `destination` (str, new absolute path) | - |
| `bulk_rename` | Batch rename files matching a pattern with sequential index `#`. | `path` (str, directory), `pattern` (str, e.g. `doc_#.txt`) | `extension` (str), `start_index` (int) |
| `delete_file` | Delete a file safely. Sends to trash by default or permanently deletes if requested. | `path` (str, absolute path) | `permanent` (bool) |
| `delete_folder` | Delete a folder safely. | `path` (str, absolute path) | `permanent` (bool) |
| `archive` | Compress a file or folder into a `.zip` archive. | `source` (str, path to compress), `destination` (str, output `.zip` path) | - |
| `extract` | Unpack and extract a `.zip` archive to a folder. | `path` (str, `.zip` path) | `destination` (str, output dir) |

---

### 2. 📂 File Management Skills & Pipelines

| Name | Type | Purpose / When to Use | Parameters |
| :--- | :--- | :--- | :--- |
| `organize_downloads` | Skill / Pipeline | Automatically sorts and organizes files in a directory (defaulting to Downloads) into categorized subfolders (`Documents`, `Images`, `Archives`, `Code`, `Audio`, `Video`, `Others`). | `source_dir` (str), `target_dir` (str, optional) |

---

### 3. 💬 WhatsApp Module Tools & Skills

*Managed via Puppeteer DOM Sidecar on port `4097`.*

| Tool Name | Purpose / When to Use | Parameters |
| :--- | :--- | :--- |
| `send_message` | Send a text message to a contact or phone number on WhatsApp. | `to` (str, contact name or phone number with country code), `message` (str, text to send) |
| `send_file` | Send a local file (PDF, image, docx, etc.) to a contact or phone number on WhatsApp. | `to` (str, contact name or phone number), `path` (str, absolute file path) |
| `list_chats` | List recent active conversations from WhatsApp. | *(none)* |
| `get_messages` | Fetch recent messages from a specific conversation. | `chat` (str, contact/chat name), `limit` (int, optional, default 10) |
| `search_messages` | Search for messages matching a text query in a chat. | `chat` (str), `query` (str) |
| `get_status` | Check WhatsApp Web connection and QR login state. | *(none)* |
| `send_report` | **Skill**: Summarize a folder/file and send the executive summary directly to a WhatsApp recipient. | `to` (str, recipient), `path` (str, target folder/file) |
| `unread_digest` | **Skill**: Collect unread WhatsApp messages and generate a concise digest. | `to` (str, optional recipient to send digest to) |

---

### 4. ✉️ Gmail Module Tools & Skills

*Managed via Google Gmail OAuth (`backend/token.json`).*

| Tool Name | Purpose / When to Use | Parameters |
| :--- | :--- | :--- |
| `send_email` | Send an email with optional attachments, subject, and body text. | `to` (str, recipient email), `body` (str, email content), `subject` (str, optional subject), `attachments` (list of str paths, optional) |
| `list_recent_emails` | **Skill**: Search and fetch recent emails from Gmail inbox matching a query (e.g. `in:inbox`, `from:boss`, `is:unread`). | `query` (str, default `"in:inbox"`), `max_results` (int, default 10) |

---

### 5. ⚡ Autonomous Background Worker Delegation (`fork`)

| Tool Name | Purpose / When to Use | Parameters |
| :--- | :--- | :--- |
| `fork` | Spawn an autonomous background worker (`antigravity_worker` or `opencode_worker`) to execute complex multi-step coding, web scraping, data analysis, script generation, or document creation in `D:/workspace`. | `objective` (str, detailed task description), `fs_scope` (str, default `"D:/workspace"`), `worker_type` (str, default `"antigravity_worker"`), `max_steps` (int, default 20) |

#### Worker Delegation Triggers (Examples):
- *"Build a python web scraper for tech news"* → `fork`
- *"Create a calculator app with HTML, CSS, JS"* → `fork`
- *"Write a script to convert CSV files into JSON"* → `fork`
- *"Refactor the backend authentication module and add unit tests"* → `fork`
- *"Generate a comprehensive docx research summary on AI trends"* → `fork`
- *"Analyze sales_data.csv and create charts"* → `fork`

---

## 📋 Standard Output Formats for Jarvis Brain

### Structured Plan Output:
```json
{
  "type": "plan",
  "reasoning": "Explain why this tool or worker was chosen.",
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

## 🔒 Safety & Boundary Constraints
1. **Path Safety**: All file operations must stay within valid drives/workspaces (e.g. `D:/workspace` or user-specified absolute paths). Protected system paths (e.g. Windows system folders) are rejected by the backend validation layer.
2. **Deterministic Parameters**: When required parameters are known from the user's prompt or recent context, populate them completely. If critical information is missing, ask a concise clarifying question.
