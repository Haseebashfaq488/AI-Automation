"""Semantic tool selector: FAISS index over tool example phrases.

Loaded once at startup (lazy), re-used for every analyze_prompt call.
Search takes ~1ms for ~200 example vectors across all known tools.
"""

from __future__ import annotations

import os
import logging
from typing import Optional, Tuple, Dict, List, Any

logger = logging.getLogger(__name__)

# Configurable confidence threshold for vector matching (0.0 to 1.0)
DEFAULT_THRESHOLD = float(os.getenv("VECTOR_CONFIDENCE_THRESHOLD", "0.58"))
MODEL_NAME = os.getenv("VECTOR_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Global singleton state
_index = None
_tool_labels: List[str] = []
_embedder = None
_initialized = False

# ── Complete Tool Corpus ───────────────────────────────────────────────────────
TOOL_CORPUS: Dict[str, List[str]] = {
    # ── Fork / Background Workers (All Filesystem, Coding, & Complex Tasks) ───
    "fork": [
        "build a calculator app",
        "create a Python script that scrapes data",
        "create a python web scraping script for news articles",
        "develop a REST API for user authentication",
        "write code to parse CSV files",
        "make a tool that monitors folder changes",
        "generate a report from the database",
        "automate my downloads folder with a custom script",
        "refactor the user module",
        "analyze my sales data and generate insights",
        "compile the project and fix errors",
        "create a full stack web app",
        "write unit tests for the backend",
        "build a modern frontend interface",
        "generate a docx document summarizing the findings",
        "fix the bugs in the application",
        "write a python script to process files",
        "list files in Downloads",
        "show what is in D drive",
        "what files are in the workspace",
        "ls D:/projects",
        "show the contents of the directory",
        "list the files in folder",
        "view directory contents",
        "what is inside D:/workspace",
        "does haseeb.txt exist on D",
        "check if report.pdf is in D:/workspace",
        "is there a file called notes.txt",
        "confirm the file exists",
        "is haseeb.txt on the D partition",
        "verify if document exists",
        "check existence of folder",
        "get file size of report.pdf",
        "show metadata for notes.txt",
        "when was this file modified",
        "check file properties and details",
        "read the file at D:/notes.txt",
        "open report.md",
        "show me the contents of config.json",
        "print the log file",
        "read file content",
        "display contents of script.py",
        "find all PDF files in Downloads",
        "search for txt files in D:/projects",
        "look for files matching *.log",
        "find files by name pattern",
        "locate all python scripts in workspace",
        "find files containing the word invoice",
        "search for 'error' inside log files",
        "look for TODO comments in D:/workspace",
        "grep for keyword in directory",
        "find text inside files",
        "create a new file called notes.txt",
        "make a blank file at D:/workspace/todo.txt",
        "touch a new file",
        "create an empty file",
        "create a new directory called backups",
        "make a new folder in D:/workspace",
        "mkdir projects",
        "create folder named reports",
        "write content into notes.txt",
        "save this text into output.txt",
        "overwrite the file with new text",
        "append line to log.txt",
        "add this note to the end of notes.md",
        "append text to file",
        "delete D:/workspace/old.txt",
        "remove the file notes.txt",
        "trash the log file",
        "delete file from disk",
        "delete the folder old_backups",
        "remove directory D:/workspace/temp",
        "trash the folder",
        "move report.pdf from Downloads to D:/workspace",
        "relocate the file to another folder",
        "move file to destination",
        "copy backup.zip to D:/archive",
        "duplicate the config file",
        "copy file to another location",
        "rename old.txt to new.txt",
        "change the file name of report.docx",
        "rename folder to archive",
        "bulk rename all images to photo_#.jpg",
        "rename multiple files sequentially",
        "batch rename files in folder",
        "organize my downloads folder",
        "sort the files in Downloads",
        "clean up Downloads folder",
        "categorize files in directory by type",
        "zip the workspace folder",
        "compress D:/projects into an archive",
        "create a zip file of the reports",
        "archive folder into zip",
        "unzip the archive",
        "extract backup.zip",
        "unpack the zip file into destination",
        "uncompress zip archive",
    ],

    # ── WhatsApp ──────────────────────────────────────────────────────────────
    "send_message": [
        "send a whatsapp message to haseeb",
        "send a whatsapp to zahida",
        "send a whatsapp",
        "send a message on whatsapp",
        "ping Zahida on WhatsApp",
        "drop a message to Ahmed on WhatsApp",
        "text my mom on WhatsApp",
        "tell Haseeb I will be late on WhatsApp",
        "WhatsApp Zahida Ashfaq",
        "send a chat to Ali on WhatsApp",
        "message the team on WhatsApp",
        "send a WhatsApp message to John",
        "text Sarah that I arrived",
        "drop a WhatsApp to boss",
    ],
    "send_file": [
        "send the report to Ahmed on WhatsApp",
        "share the PDF with Zahida",
        "forward the document to Ali via WhatsApp",
        "drop the invoice file to the group",
        "send this photo to mom on WhatsApp",
        "share the docx file with boss on WhatsApp",
        "attach file and send to Zahida on WhatsApp",
    ],
    "list_chats": [
        "show my WhatsApp chats",
        "list all WhatsApp chats",
        "what conversations do I have",
        "who have I been talking to on WhatsApp",
        "view recent WhatsApp chats",
        "get my chat list",
    ],
    "get_messages": [
        "show messages from Zahida",
        "what did Ali say on WhatsApp",
        "read the chat with Ahmed",
        "get last 10 messages from the group",
        "view recent messages in chat",
        "fetch chat history with Sarah",
    ],
    "search_messages": [
        "search for meeting in WhatsApp chats",
        "find message containing password",
        "search chat history for invoice",
        "look for keyphrase in messages",
    ],
    "get_unread_messages": [
        "check my unread WhatsApp messages",
        "what are my unread chats on WhatsApp",
        "show unread messages using WhatsApp unread filter",
        "do I have any new unread WhatsApp messages",
        "filter unread WhatsApp messages",
        "fetch unread WhatsApp conversations",
    ],
    "get_recent_whatsapp_activity": [
        "what happened on WhatsApp over the past 3 days",
        "show recent WhatsApp activity for Today, Yesterday, and Tuesday",
        "summarize active WhatsApp chats and groups",
        "what was the activity in my WhatsApp conversations recently",
        "get recent WhatsApp activity across all groups",
    ],
    "get_whatsapp_chat_messages": [
        "get WhatsApp messages from FAST CFD ALL BATCHES",
        "fetch chat messages from Rao Waleed",
        "show conversation dialogue from FYP Ki Chussein",
        "what did they say in Ahmad Fiaz chat",
        "get recent chat dialogue for contact",
    ],
    "send_report": [
        "send project report to Zahida",
        "summarize folder and WhatsApp to Ahmed",
        "generate summary report and send to client on WhatsApp",
    ],
    "unread_digest": [
        "what are my unread messages",
        "summarize unread WhatsApp messages",
        "show unread chats",
        "give me a digest of unread WhatsApp",
    ],

    # ── Gmail ──────────────────────────────────────────────────────────────────
    "send_email": [
        "send a mail to zahidaashfaq@gmail.com",
        "send a mail to zahida ashfaq",
        "send a mail to zahida ashfaq content is haseeb",
        "send an email to john@example.com",
        "email the report to the client",
        "mail Ahmed about the meeting",
        "compose an email to HR",
        "send Gmail to boss@company.com",
        "forward email with attachment",
        "drop an email to support",
        "send email to test@domain.com saying hello",
        "send a mail",
        "send an email",
        "email to someone",
    ],
    "list_recent_emails": [
        "show my inbox",
        "what emails did I get",
        "check my Gmail inbox",
        "any new emails in Gmail",
        "search for emails from Ahmed",
        "list recent emails",
        "fetch unread emails",
    ],

    # ── Google Drive ───────────────────────────────────────────────────────────
    "list_drive_files": [
        "list files in my google drive",
        "show files from google drive",
        "what files do i have in drive",
        "list drive files",
        "show drive contents",
        "get google drive documents",
        "list 10 files from drive",
    ],
    "read_drive_file": [
        "read my google doc",
        "download file from drive",
        "get drive file content",
        "read the drive document",
        "fetch file from google drive",
    ],
    "upload_drive_file": [
        "upload this file to google drive",
        "save file to drive",
        "upload document to my drive folder",
        "backup file to google drive",
    ],
    "search_drive": [
        "search google drive for roadmap",
        "find invoice on drive",
        "search drive files for reports",
        "look for pdf files in drive",
        "search drive for presentation",
    ],
}


# Precomputed embeddings matrix and label array
_phrase_embeddings: Optional[Any] = None


def _build_index(corpus: Dict[str, List[str]]) -> bool:
    """Encode all example phrases with ONNX embedder into a normalized NumPy matrix."""
    global _phrase_embeddings, _tool_labels, _embedder, _initialized

    try:
        import numpy as np
        from app.modules.antigravity.onnx_embedder import get_onnx_embedder
        _embedder = get_onnx_embedder()
    except Exception as exc:
        logger.warning("ONNX tool embedder unavailable: %s", exc)
        return False

    try:
        phrases: List[str] = []
        labels: List[str] = []
        for tool, examples in corpus.items():
            for phrase in examples:
                phrases.append(phrase)
                labels.append(tool)

        vecs = _embedder.encode(phrases, normalize_embeddings=True)
        _phrase_embeddings = np.array(vecs, dtype=np.float32)
        _tool_labels = labels
        _initialized = True
        logger.info("Built ONNX tool vector index with %d phrases across %d tools. ⚡", len(phrases), len(corpus))
        return True
    except Exception as exc:
        logger.error("Failed to build ONNX tool vector index: %s", exc, exc_info=True)
        return False


def get_index(corpus: Optional[Dict[str, List[str]]] = None) -> Any:
    """Return or lazily initialize the global ONNX tool index matrix."""
    global _phrase_embeddings, _initialized
    if not _initialized or _phrase_embeddings is None:
        c = corpus or TOOL_CORPUS
        _build_index(c)
    return _phrase_embeddings


def query(
    prompt: str,
    corpus: Optional[Dict[str, List[str]]] = None,
    top_k: int = 3,
    threshold: Optional[float] = None,
) -> Tuple[Optional[str], float]:
    """Return (best_tool_name, confidence_score) for the given prompt using ONNX dot product.

    Returns (None, best_score) if score is below the confidence threshold.
    Returns (None, 0.0) if index is unavailable.
    """
    import numpy as np

    c = corpus or TOOL_CORPUS
    embeddings = get_index(c)
    if embeddings is None or _embedder is None or not _tool_labels:
        return None, 0.0

    min_threshold = threshold if threshold is not None else DEFAULT_THRESHOLD

    try:
        q_vec = _embedder.encode(prompt, normalize_embeddings=True)
        sims = np.dot(embeddings, q_vec)
        best_idx = int(np.argmax(sims))
        best_score = float(sims[best_idx])
        best_tool = _tool_labels[best_idx]

        if best_score < min_threshold:
            return None, best_score
        return best_tool, best_score
    except Exception as exc:
        logger.warning("ONNX tool vector search query failed for prompt '%s': %s", prompt[:50], exc)
        return None, 0.0

