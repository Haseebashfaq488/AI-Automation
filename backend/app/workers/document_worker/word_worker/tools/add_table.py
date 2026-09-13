import json
from typing import Any, Dict, List, Optional

from app.core.tool import BaseTool, RiskLevel
from app.workers.document_worker.word_worker.helpers.document import open_docx, save_docx
from app.workers.document_worker.word_worker.helpers.paths import resolve_doc_path


class AddTableTool(BaseTool):
    """Insert a structured data table into an existing Word document.

    Accepts flexible input formats for headers and rows (2D list, list of dicts,
    comma-separated strings, or single-column arrays).

    Parameters
    ----------
    path: str
        Absolute path to the .docx file.
    headers: list[str] or str (optional)
        List of column header titles or comma-separated string.
    rows: list[list[any]] or list[dict] or list[str] (optional)
        Data rows for the table.
    style: str (optional)
        Word table style (default: 'Table Grid').
    fs_scope: str (optional)
        Worker scope the path must reside within.
    """

    name = "add_table"
    description = "Insert a structured table with headers and data rows into a Word document."
    risk = RiskLevel.MEDIUM
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "headers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Column header names (or comma-separated string)",
            },
            "rows": {
                "type": "array",
                "items": {"type": "array"},
                "description": "List of data rows (2D array, dict list, or text items)",
            },
            "style": {"type": "string", "default": "Table Grid"},
            "fs_scope": {"type": "string"},
        },
        "required": ["path"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_doc_path(params["path"], params.get("fs_scope"))
        doc = open_docx(path)

        # 1. Normalize headers (handle aliases: headers, columns, header, cols)
        raw_headers = (
            params.get("headers")
            or params.get("columns")
            or params.get("header")
            or params.get("cols")
        )
        headers: List[str] = []
        if isinstance(raw_headers, str):
            if "," in raw_headers:
                headers = [h.strip() for h in raw_headers.split(",") if h.strip()]
            elif "|" in raw_headers:
                headers = [h.strip() for h in raw_headers.split("|") if h.strip()]
            elif raw_headers.strip():
                headers = [raw_headers.strip()]
        elif isinstance(raw_headers, (list, tuple)):
            headers = [str(h).strip() for h in raw_headers]

        # 2. Normalize rows (handle aliases: rows, data, table, table_data, records, content)
        raw_rows = (
            params.get("rows")
            or params.get("data")
            or params.get("table")
            or params.get("table_data")
            or params.get("records")
            or params.get("content")
            or []
        )

        # If raw_rows was passed as a JSON string, decode it
        if isinstance(raw_rows, str):
            raw_rows = raw_rows.strip()
            if raw_rows.startswith("[") and raw_rows.endswith("]"):
                try:
                    raw_rows = json.loads(raw_rows)
                except Exception:
                    pass

        clean_rows: List[List[str]] = []

        if isinstance(raw_rows, list):
            for item in raw_rows:
                if isinstance(item, dict):
                    # List of dicts (e.g. [{"Name": "Alice", "Role": "Dev"}])
                    if not headers:
                        headers = list(item.keys())
                    clean_rows.append([str(item.get(h, "")) for h in headers])
                elif isinstance(item, (list, tuple)):
                    # 2D list item
                    clean_rows.append([str(c) for c in item])
                elif isinstance(item, str):
                    # String item (e.g. single column row)
                    clean_rows.append([item])
                else:
                    clean_rows.append([str(item)])
        elif isinstance(raw_rows, dict):
            # Single dict mapping headers to values
            if not headers:
                headers = list(raw_rows.keys())
            clean_rows.append([str(raw_rows.get(h, "")) for h in headers])
        elif isinstance(raw_rows, str) and raw_rows.strip():
            # Multiline text or single text block
            lines = [line.strip() for line in raw_rows.splitlines() if line.strip()]
            for line in lines:
                if "," in line:
                    clean_rows.append([c.strip() for c in line.split(",")])
                elif "|" in line:
                    clean_rows.append([c.strip() for c in line.split("|") if c.strip()])
                else:
                    clean_rows.append([line])

        # 3. If headers were not specified, derive from first row or defaults
        if not headers:
            if clean_rows:
                # If we have multiple rows, treat row 0 as header
                if len(clean_rows) > 1:
                    headers = clean_rows.pop(0)
                else:
                    headers = [f"Column {i + 1}" for i in range(len(clean_rows[0]))]
            else:
                headers = ["Column 1"]

        # Determine column count
        num_cols = max(len(headers), max((len(r) for r in clean_rows), default=0), 1)

        # Pad headers if shorter than column count
        while len(headers) < num_cols:
            headers.append(f"Column {len(headers) + 1}")

        # Pad rows if any row is shorter than column count
        for r in clean_rows:
            while len(r) < num_cols:
                r.append("")

        # 4. Construct table in Word document
        total_rows = len(clean_rows) + 1  # 1 for header row
        table = doc.add_table(rows=total_rows, cols=num_cols)

        # 5. Apply table style safely
        style_name = params.get("style", "Table Grid")
        if style_name and style_name in doc.styles:
            table.style = doc.styles[style_name]
        else:
            try:
                table.style = "Table Grid"
            except Exception:
                pass

        # 6. Populate header row (bold font)
        for col_idx, header_text in enumerate(headers):
            cell = table.cell(0, col_idx)
            cell.text = header_text
            for p in cell.paragraphs:
                for r in p.runs:
                    r.bold = True

        # 7. Populate data rows
        for row_idx, row_data in enumerate(clean_rows):
            for col_idx in range(num_cols):
                val = row_data[col_idx] if col_idx < len(row_data) else ""
                table.cell(row_idx + 1, col_idx).text = str(val)

        save_docx(doc, path)

        return {
            "path": str(path),
            "table_index": len(doc.tables) - 1,
            "total_tables": len(doc.tables),
            "rows_count": len(clean_rows),
            "cols_count": num_cols,
            "headers": headers,
        }
