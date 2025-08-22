import os
import subprocess
from typing import Optional


def grep(term: str) -> str:
    """
    Search recursively in the repository for files containing the search term.
    Returns matching lines with file path, line number, and content.
    """
    matches = []
    # Get the list of tracked files using git
    try:
        output = subprocess.check_output(['git', 'ls-files'], text=True)
        tracked_files = output.splitlines()
    except subprocess.CalledProcessError:
        return "Error retrieving tracked files."

    for filepath in tracked_files:
        # Try reading as text
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, start=1):
                    if term in line:
                        matches.append(f"{filepath}:{i}: {line.rstrip()}")
        except Exception:
            continue  # Skip unreadable files

    if matches:
        return "\n".join(matches)
    else:
        return f"No matches found for '{term}' in tracked files."


schema = {
    "type": "function",
    "function": {
        "name": "grep",
        "description": "Search tracked files for a given term and return file paths, line numbers, and matching content.",
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
