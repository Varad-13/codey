import os
from typing import Optional

def grep(term: str, path: Optional[str] = ".") -> str:
    """
    Search recursively in the given path for files containing the search term.
    Returns matching lines with file path, line number, and content.
    """
    matches = []
    for root, dirs, files in os.walk(path):
        for filename in files:
            filepath = os.path.join(root, filename)
            # Try reading as text
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f, start=1):
                        if term in line:
                            rel_path = os.path.relpath(filepath, os.getcwd())
                            matches.append(f"{rel_path}:{i}: {line.rstrip()}")
            except Exception:
                continue  # Skip unreadable files
    if matches:
        return "\n".join(matches)
    else:
        return f"No matches found for '{term}' in path '{path}'."

schema = {
    "type": "function",
    "name": "grep",
    "description": "Recursively search files for a given term and return file paths, line numbers, and matching content.",
    "parameters": {
        "type": "object",
        "properties": {
            "term": {"type": "string", "description": "The search term to look for in files."},
            "path": {"type": "string", "description": "The directory path to search in (default is current directory)."}
        },
        "required": ["term"],
        "additionalProperties": False
    }
}