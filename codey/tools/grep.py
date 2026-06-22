import os
import subprocess
from pathlib import Path

MAX_FILE_SIZE = 1 * 1024 * 1024
BINARY_SCAN_BYTES = 8192
MAX_MATCHES = 200


def _looks_binary(head_bytes: bytes) -> bool:
    return b"\x00" in head_bytes


def grep(
    term: str,
    regex: bool = False,
    case_insensitive: bool = False,
    base_dir: str = None,
) -> str:
    """
    Search the repository for files containing the search term.

    Defaults to literal substring search (NOT regex). Set regex=True to use
    a Python regular expression. Skip files larger than 1 MB and binary
    files (null bytes in first 8 KB). Caps total matches returned at 200
    with a footer indicating the truncated count.
    """
    if base_dir is None:
        base_dir = os.getcwd()
    base_path = Path(base_dir).resolve()

    try:
        tracked = subprocess.run(
            ['git', 'ls-files'],
            capture_output=True, text=True,
            cwd=str(base_path), timeout=10, check=False,
        )
        if tracked.returncode != 0:
            return f"Error retrieving file list: {tracked.stderr.strip()}"
        untracked = subprocess.run(
            ['git', 'ls-files', '--others', '--exclude-standard'],
            capture_output=True, text=True,
            cwd=str(base_path), timeout=10, check=False,
        )
        if untracked.returncode != 0:
            return f"Error retrieving untracked file list: {untracked.stderr.strip()}"
    except FileNotFoundError:
        return "Error: 'git' is not installed or not on PATH. Install git and retry."
    except subprocess.TimeoutExpired:
        return "Error: 'git ls-files' timed out after 10 seconds."
    except Exception as e:
        return f"Error retrieving file list: {e}"

    all_files = list(dict.fromkeys(
        [f.strip() for f in tracked.stdout.splitlines() if f.strip()]
        + [f.strip() for f in untracked.stdout.splitlines() if f.strip()]
    ))

    # Compile matcher once
    if regex:
        import re
        flags = re.IGNORECASE if case_insensitive else 0
        try:
            pattern = re.compile(term, flags=flags)
        except re.error as e:
            return f"Error: invalid regex: {e}"
        def match(line: str) -> bool:
            return pattern.search(line) is not None
    else:
        needle = term.lower() if case_insensitive else term
        def match(line: str) -> bool:
            return needle in (line.lower() if case_insensitive else line)

    matches = []
    files_searched = 0
    files_skipped = 0
    for relpath in all_files:
        target = (base_path / relpath).resolve()
        if not target.is_file():
            continue
        try:
            size = target.stat().st_size
        except OSError:
            continue
        if size > MAX_FILE_SIZE:
            files_skipped += 1
            continue
        try:
            with open(target, "rb") as f:
                head = f.read(BINARY_SCAN_BYTES)
            if _looks_binary(head):
                files_skipped += 1
                continue
            with open(target, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, start=1):
                    if match(line):
                        matches.append(f"{relpath}:{i}: {line.rstrip()}")
                        if len(matches) >= MAX_MATCHES:
                            break
        except (IOError, OSError, UnicodeDecodeError):
            files_skipped += 1
            continue
        files_searched += 1
        if len(matches) >= MAX_MATCHES:
            break

    summary = {
        "files_searched": files_searched,
        "files_skipped_large_or_binary": files_skipped,
        "match_count": len(matches),
        "capped_at": MAX_MATCHES,
        "literal": not regex,
        "case_insensitive": case_insensitive,
    }

    if not matches:
        return f"No matches found for '{term}'.\n[structured] {summary}"

    body = "\n".join(matches)
    if len(matches) >= MAX_MATCHES:
        # Note: the actual count could exceed MAX_MATCHES since we break inside
        # the inner loop after the first batch exceeds it. Report truncation.
        return (
            f"{body}\n\n... (results capped at {MAX_MATCHES}; "
            f"refine the search term or scope to see more)\n[structured] {summary}"
        )
    return f"{body}\n[structured] {summary}"


schema = {
    "type": "function",
    "function": {
        "name": "grep",
        "description": "Search tracked and untracked repository files for a term. Defaults to literal substring search (NOT regex). Set regex=True for regex, case_insensitive=True to ignore case. Skips files larger than 1 MB and binary files; caps results at 200.",
        "parameters": {
            "type": "object",
            "properties": {
                "term": {
                    "type": "string",
                    "description": "The search term to look for in files (literal substring by default)."
                },
                "regex": {
                    "type": "boolean",
                    "description": "If true, treat term as a Python regular expression. Defaults to false (literal substring).",
                    "default": False
                },
                "case_insensitive": {
                    "type": "boolean",
                    "description": "If true, match case-insensitively. Defaults to false.",
                    "default": False
                },
                "base_dir": {
                    "type": "string",
                    "description": "Project root directory (defaults to current working directory)."
                }
            },
            "required": ["term"],
            "additionalProperties": False
        }
    }
}
