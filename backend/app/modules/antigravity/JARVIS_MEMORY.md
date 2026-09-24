# 🧠 JARVIS LIVING MEMORY & SYSTEM CONTEXT

> This document serves as Jarvis's persistent long-term memory across sessions. It is read dynamically and updated autonomously when new knowledge or preferences are learned.

---

## 👤 User Profile & Preferences
- **Owner / User**: Haseeb
- **Phone Number**: +923098956995 (Self-chat / Primary WhatsApp recipient)
- **Primary Workspace**: `D:/workspace` (clean dedicated directory for autonomous workers)
- **Preferred LLMs**: `gemini-3.8-flash-low` (Fast / Default), `gemini-3.8-flash-high`, `gemini-3.1-pro-high`, `claude-sonnet-4-6`
- **Execution Style**: Fast, concise, direct execution with zero unnecessary directory scanning.

---

## 🛠️ Integrated Capabilities & Active Tools
- **Google Drive Integration** (`backend/drive_token.json`):
  - `list_drive_files`: List and filter Drive files and folders with size formatting, metadata, and web links.
  - `read_drive_file`: Read Google Docs/Sheets content or download files to local paths.
  - `upload_drive_file`: Upload local files to specific Drive folders.
  - `search_drive`: Search Drive files by name, full-text content, and file type filters.
- **WhatsApp Sidecar** (`http://127.0.0.1:4097`):
  - `send_message`: Send messages to phone numbers or chat names.
  - `send_file`: Send documents / attachments.
  - `list_chats`: List recent chats and unread conversations.
  - `get_messages`: Retrieve chat message history.
- **Gmail Integration** (`backend/token.json`):
  - `send_email`: Send email with optional attachments (up to 25MB).
  - `list_recent_emails`: Search and read inbox messages (`query: "in:inbox"`).
- **File Management & System**:
  - Direct file operations in `D:/workspace` and project boundaries.
  - Safe operations with dry-run support and protected path guards.
- **Autonomous Background Workers**:
  - Isolated background worker engine (`D:/workspace`) powered by pure Antigravity CLI (`agy.exe`).

---

## 📌 Active Knowledge & Notes
- [2026-09-23] Google Drive OAuth authenticated with dedicated token (`backend/drive_token.json`); Drive tools active.
- [2026-09-16] Dedicated `D:/workspace` established as fast working directory for all workers.
- [2026-09-16] Pure `agy.exe` subprocess driver active with session persistence across milestones.
- [2026-09-16] `JARVIS_MEMORY.md` configured as living brain scratchpad.
- [2026-09-22] Memory extraction reinforcement loop activated — Jarvis extracts durable facts after every turn via `agy` daemon.

## 📜 Core Operational Rules (Manager Persona)
1. **Manager Role Only**: Jarvis does NOT do task reasoning, coding, document writing, or execution himself in chat.
2. **Known Tools Execution**: Jarvis only plans actions using predefined, known tools (Google Drive, WhatsApp, Gmail, File operations, and `fork`).
3. **Automatic Worker Delegation**: Whenever the user requests any task, project, script, document, calculation, coding, or automation workflow, Jarvis MUST generate a tool plan using `fork` targeting `D:/workspace` (`worker_type="antigravity_worker"`).
4. **User Confirmation**: All tool executions and worker forks require user acceptance via the plan card before the worker executes.
5. **Worker Execution**: Once accepted, the background worker performs the entire task autonomously in `D:/workspace`.

---

## 📝 Scratchpad & Temporary Notes
- [2026-09-24 18:42] Worker [ws_c6963728a1a7] resolved: Create a simple text file named 'document.txt' in D:/workspace with clean, representative placeholder content.
- [2026-09-24 18:12] Worker [ws_046b286356f9] resolved: Create a file named 'document.txt' on local disk D (in 'D:/workspace') populated with clean, representative content.
- [2026-09-24 18:11] User frequently combines file generation workflows with multi-channel distribution across Email and Google Drive.
- [2026-09-24 17:52] Worker [ws_21e10b045e45] resolved: Create a file in D:/ with representative content.
- [2026-09-24 17:29] Worker [ws_71f701ca87a4] resolved: Create the requested file in 'D:/workspace' with appropriate, structured content.
- [2026-09-24 17:23] Worker [ws_57cf6771aadf] resolved: Create a simple text file named 'sample.txt' in D:/workspace with clean, representative placeholder content.
- [2026-09-24 17:20] Worker [ws_de5cd263bc12] resolved: Create a simple text file named 'sample.txt' in D:/workspace with clean, representative placeholder content.
- [2026-09-24 17:11] Worker [ws_9f344fbd3e10] resolved: make a file in local disk D say haseeb321.txt and put dummy content in it okey.
- [2026-09-24 17:07] Worker [ws_2d991cdbeb6a] resolved: Create a file named 'tem123.txt' (or 'tem123') in 'D:/' and populate it with appropriate dummy/placeholder content.
- [2026-09-24 16:53] Worker [ws_2cd20d897cee] resolved: Create a temporary text file named 'temp.txt' in 'D:/workspace' and populate it with dummy placeholder content.
- [2026-09-24 15:45] Worker [ws_74ecdb4cbdd2] resolved: Create a temporary file named 'temp.txt' directly in the root path 'D:/' containing standard Lorem Ipsum placeholder text.
- [2026-09-24 11:00] User is a member of an ICPC participants WhatsApp group.
- [2026-09-24 10:28] User has a WhatsApp group named 'bois'.
- [2026-09-23 15:57] Worker [ws_870d70b49fca] resolved: Create a file named 'hello.docx' in 'D:/workspace' containing approximately one full page of well-formatted dummy/placeholder content.
- [2026-09-23 15:44] User utilizes tri-channel delivery (WhatsApp, Email, and Google Drive) for generated document artifacts.
- [2026-09-23 15:03] Worker [ws_8812622959f1] resolved: Create a dummy file named 'dummy.txt' in D:/workspace with appropriate sample placeholder content.
- [2026-09-23 14:57] Worker [ws_7222aa9abd0f] resolved: Create a file named 'dummm.txt' in D:/workspace with appropriate initial or placeholder content.
- [2026-09-23 14:47] Worker [ws_2f748e88a775] resolved: Create a file named 'dummm.txt' in D:/workspace with appropriate initial or placeholder content.
- [2026-09-23 14:23] Worker [ws_e6d07e6717cb] resolved: Analyze the frontend codebase located in 'D:/AI-Automation' (examining the frontend directory, components, architecture, and project structure). Generate a comprehensive analysis report markdown file named 'D:/workspace/AI_Automation_Frontend_Report.md'.
- [2026-09-23 14:21] User prefers dual-channel delivery (WhatsApp and Email) when requesting project analysis reports.
- [2026-09-23 14:21] User maintains a frontend codebase located within 'D:/AI-Automation'.
- [2026-09-23 13:51] Worker [ws_753fb2c36101] resolved: Analyze the codebase and project structure in 'D:/AI-Automation', examining graphify and related components to understand the project architecture. Generate a comprehensive summary report file named 'D:/workspace/AI_Automation_Report.md'.
- [2026-09-23 13:46] User leverages graphify within 'D:/AI-Automation' as the primary comprehension tool for codebase analysis tasks.
- [2026-09-23 13:46] User requests concurrent multi-channel delivery (Email and WhatsApp) for major project reports and analyses.
- [2026-09-23 13:27] this is my mail
- [2026-09-23 13:26] Haseeb's primary email address is haseebhamza789@gmail.com.
- [2026-09-23 13:23] Worker [ws_1fc62343bf8d] resolved: Open 'D:/workspace/document.txt' and add comprehensive dummy content to it.
- [2026-09-23 13:21] Worker [ws_31334d4b6c34] resolved: Create a file named 'document.txt' in D:/workspace with an initial structure.
- [2026-09-23 13:20] User utilizes email workflows for receiving generated file artifacts in addition to WhatsApp.
- [2026-09-23 13:20] User prefers dividing file generation into sequential worker stages (creation followed by content population) before outbound communication.
- [2026-09-23 10:50] Worker [ws_af5bc454c2c7] resolved: Open the newly created document file in D:/workspace and write comprehensive, detailed content into it.
- [2026-09-23 10:48] Multi-worker file generation workflows should culminate in sending the resulting artifact to the user via WhatsApp (+923098956995).
- [2026-09-23 10:48] User prefers dividing file tasks into sequential worker stages: an initialization worker to create structure followed by a second worker to write detailed content before delivery.
- [2026-09-23 10:43] Worker [ws_eb16f07aee71] resolved: Create a file named 'haseeb.txt' in D:/workspace with basic placeholder structure.
- [2026-09-23 10:40] Worker [ws_fb8f909b890b] resolved: Create a file named 'quotes.txt' in D:/workspace with basic placeholder structure.
- [2026-09-23 10:26] Worker [ws_d87bd09c9f93] resolved: Create the file in D:/workspace with appropriate content.
- [2026-09-23 10:18] Worker [ws_74a7cbf9b12b] resolved: Create the requested file in D:/workspace with appropriate content.
- [2026-09-23 10:08] Worker [ws_7cd4c864b8fb] resolved: Create a file named 'dum.txt' with sample content in D:/workspace.
- [2026-09-23 10:01] Worker [ws_07551b26889e] resolved: Create a file named 'Umair.txt' with appropriate greeting/placeholder content in D:/workspace.
- [2026-09-23 09:52] Worker [test_worker_123] resolved: Build parser
- [2026-09-23 09:21] Worker [ws_b3edb12e6e2e] resolved: Create a dummy file named 'report.txt' in D:/workspace with clean sample report content.
- [2026-09-23 09:20] Autonomous background workers only generate files and perform coding/tasks; sending communication files must be planned as explicit manager tools like send_file.
- [2026-09-22 22:01] The user's name is Haseeb, and he is the owner and operator of this system.
