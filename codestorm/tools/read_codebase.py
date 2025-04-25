import subprocess
import os

def read_codebase() -> str:
    """
    List tracked files in the current git repository.
    If the repo is empty, initialize it and notify.
    Runs commands with CWD as user's current working directory.
    """
    base_dir = os.getcwd()
    proc = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        cwd=base_dir,
    )
    files = [f.strip() for f in proc.stdout.splitlines() if f.strip()]
    if not files:
        # Empty repo initialize and report
        subprocess.run(["git", "init"], check=True, cwd=base_dir)
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
