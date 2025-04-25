# tools/read_codebase.py

import subprocess
import os

def read_codebase() -> str:
    """
    List tracked files in the current git repository.
    If the repo is empty, initialize it and notify.
    """
    proc = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
    )
    files = [f.strip() for f in proc.stdout.splitlines() if f.strip()]
    if not files:
        # Empty repo → initialize and report
        subprocess.run(["git", "init"], check=True)
        return "Initialized empty git repository. No files to list yet."
    return "\n".join(files)

schema = {
    "type": "function",
    "name": "read_codebase",
    "description": "List files in the git repository (inits if empty).",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False
    }
}
