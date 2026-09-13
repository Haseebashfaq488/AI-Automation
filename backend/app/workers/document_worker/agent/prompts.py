TOOL_SIGNATURES = {
    "create_docx": "create_docx(path, title=None, initial_text=None)",
    "add_heading": "add_heading(path, text, level=1)",
    "add_paragraph": "add_paragraph(path, text, style='Normal', bold=False, italic=False)",
    "add_table": "add_table(path, headers=['Col1', 'Col2'], rows=[['Val1', 'Val2']])",
    "inspect_docx": "inspect_docx(path)",
    "read_docx": "read_docx(path, start=0, limit=200)",
    "normalize_headings": "normalize_headings(path)",
    "fix_spacing": "fix_spacing(path)",
    "format_tables": "format_tables(path, style='Table Grid')",
    "backup_docx": "backup_docx(path)",
    "list_directory": "list_directory(path)",
    "exists": "exists(path)",
}


def worker_system_prompt(available_tools: list[str], objective: str, files_in_scope: list[str] | None = None) -> str:
    """Tiny, scope‑locked system prompt for the document worker (per the
    parent‑worker design: the worker must NOT think outside its scope)."""
    tool_lines = "\n".join(f"- {TOOL_SIGNATURES.get(t, t)}" for t in available_tools)
    if files_in_scope:
        file_lines = "\n".join(f"- {f}" for f in files_in_scope[:20])
        files_block = f"\nFILES ALREADY IN YOUR SCOPE (use these exact absolute paths):\n{file_lines}\n"
    else:
        files_block = ""
    return (
        "You are the Document Worker, a Microsoft Word specialist agent.\n"
        "You operate strictly inside the task assigned by the parent agent.\n\n"
        f"YOUR ASSIGNED TASK:\n{objective}\n\n"
        f"TOOLS YOU MAY USE (no others exist for you):\n{tool_lines}\n"
        f"{files_block}\n"
        "RULES:\n"
        "1. Complete ONLY the assigned task. Do not explore, refactor, or improve anything else.\n"
        "2. Before modifying a document, call backup_docx unless the parent said otherwise.\n"
        "3. Work step by step: inspect first, then modify, then verify by re‑inspecting.\n"
        "4. If a tool fails twice, STOP and report failure — do not retry endlessly.\n"
        "5. Respect the fs_scope parameter — never touch files outside it.\n"
        "6. ALWAYS pass the absolute file path in every tool call's \"path\" param.\n"
        "7. NEVER use function/tool calling — your entire reply must be plain text "
        "containing only the JSON object.\n\n"
        "RESPONSE FORMAT (return ONLY this JSON, no markdown fences):\n"
        '{"action": "tool", "tool": "<tool_name>", "params": {<params>}}\n'
        'or when the task is complete:\n'
        '{"action": "done", "summary": "<what was accomplished>"}'
    )


def decision_user_message(step_results: list[dict], contract_summary: str) -> str:
    """Compact worker context — step results only, never parent history."""
    lines = [f"Task: {contract_summary}", "", "Steps so far:"]
    if not step_results:
        lines.append("(none — this is the first step)")
    for i, r in enumerate(step_results):
        if r.get("success"):
            line = f"{i + 1}. {r.get('tool')} → ok"
            out = r.get("output")
            if isinstance(out, str) and out.strip():
                line += f" — {out[:150]}"
            elif isinstance(out, dict) and out:
                brief = ", ".join(f"{k}={v}" for k, v in list(out.items())[:6] if not str(k).startswith("_"))
                line += f" — {brief[:200]}"
        else:
            line = f"{i + 1}. {r.get('tool')} → FAILED: {r.get('error', 'unknown')}"
        lines.append(line)
    lines.append("")
    lines.append("Decide the next single step as JSON.")
    return "\n".join(lines)