from typing import Dict, Any, List
from app.core.tool import BaseTool, RiskLevel
from app.modules.file_management.helpers.paths import resolve_path
from app.modules.file_management.helpers.validation import ensure_exists


class SearchContentTool(BaseTool):
    name = "search_content"
    description = "Search for text inside files, like grep (returns file, line number, and line text)."
    risk = RiskLevel.LOW

    # Skip files larger than 5 MB and files that look binary.
    MAX_FILE_BYTES = 5 * 1024 * 1024

    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "file or directory to search in"},
            "query": {"type": "string", "description": "text to find"},
            "recursive": {"type": "boolean", "default": True},
            "case_sensitive": {"type": "boolean", "default": False},
            "max_results": {"type": "integer", "default": 100},
        },
        "required": ["path", "query"],
    }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_path(params["path"])
        ensure_exists(path)
        query = params["query"]
        recursive = params.get("recursive", True)
        case_sensitive = params.get("case_sensitive", False)
        max_results = int(params.get("max_results", 100))
        needle = query if case_sensitive else query.lower()

        if path.is_file():
            candidates = [path]
        elif recursive:
            candidates = path.rglob("*")
        else:
            candidates = path.glob("*")

        matches: List[Dict[str, Any]] = []
        skipped_files: List[str] = []
        files_searched = 0

        for f in candidates:
            if len(matches) >= max_results:
                break
            try:
                if not f.is_file():
                    continue
                if f.stat().st_size > self.MAX_FILE_BYTES:
                    skipped_files.append(str(f))
                    continue
                with f.open("r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read(self.MAX_FILE_BYTES + 1)
                if "\0" in content[:8192]:  # binary file
                    skipped_files.append(str(f))
                    continue
                files_searched += 1
                for lineno, line in enumerate(content.splitlines(), start=1):
                    haystack = line if case_sensitive else line.lower()
                    if needle in haystack:
                        matches.append({
                            "file": str(f),
                            "line": lineno,
                            "text": line.strip()[:200],
                        })
                        if len(matches) >= max_results:
                            break
            except OSError:
                skipped_files.append(str(f))

        return {
            "path": str(path),
            "query": query,
            "recursive": recursive,
            "case_sensitive": case_sensitive,
            "files_searched": files_searched,
            "match_count": len(matches),
            "matches": matches,
            "truncated": len(matches) >= max_results,
            "skipped_files": skipped_files,
        }
