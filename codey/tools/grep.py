import os
import subprocess


def grep(term: str) -> str:
    """
    Search the repository for files containing the search term.
    Covers both git-tracked files and untracked (non-ignored) files.
    Returns matching lines with file path, line number, and content.
    """
    try:
        tracked = subprocess.check_output(
            ['git', 'ls-files'], text=True
        ).splitlines()
        untracked = subprocess.check_output(
            ['git', 'ls-files', '--others', '--exclude-standard'], text=True
        ).splitlines()
    except subprocess.CalledProcessError:
        return "Error retrieving file list."

    # Deduplicate while preserving order
    all_files = list(dict.fromkeys(tracked + untracked))

    matches = []
    for filepath in all_files:
        if not os.path.isfile(filepath):
            continue
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, start=1):
                    if term in line:
                        matches.append(f"{filepath}:{i}: {line.rstrip()}")
        except (IOError, OSError):
            continue

    if matches:
        return "\n".join(matches)
    return f"No matches found for '{term}'."


schema = {
    "type": "function",
    "function": {
        "name": "grep",
        "description": "Search tracked and untracked repository files for a given term. Returns file paths, line numbers, and matching content.",
        "parameters": {
            "type": "object",
            "properties": {
                "term": {
                    "type": "string",
                    "description": "The search term to look for in files."
                }
            },
            "required": ["term"],
            "additionalProperties": False
        }
    }
}
