import subprocess
import os


def read_codebase(base_dir: str = None, cwd: str = None) -> str:
    """
    List tracked files in the current git repository.
    Returns a clear message if no tracked files are found (does NOT auto-init).
    Runs commands with CWD as the resolved base directory.
    """
    if base_dir is None:
        base_dir = os.getcwd()
    if cwd is None:
        cwd = base_dir

    try:
        proc = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
            check=False,
        )
    except FileNotFoundError:
        return "Error: 'git' is not installed or not on PATH. Install git and retry."
    except subprocess.TimeoutExpired:
        return "Error: 'git ls-files' timed out after 10 seconds."
    except Exception as e:
        return f"Error running git ls-files: {e}"

    files = [f.strip() for f in proc.stdout.splitlines() if f.strip()]
    summary = {
        "base_dir": base_dir,
        "cwd": cwd,
        "git_returncode": proc.returncode,
        "count": len(files),
    }
    if not files:
        return (
            "No tracked files; repository appears uninitialized or empty. "
            "Run `git init` if you want to initialize.\n"
            f"[structured] {summary}"
        )
    return "\n".join(files) + f"\n[structured] {summary}"


schema = {
    "type": "function",
    "function": {
        "name": "read_codebase",
        "description": "List tracked files in the git repository. Returns a clear message if the repo is empty or uninitialized (does NOT auto-initialize).",
        "parameters": {
            "type": "object",
            "properties": {
                "base_dir": {
                    "type": "string",
                    "description": "Project root directory (defaults to current working directory)."
                },
                "cwd": {
                    "type": "string",
                    "description": "Subdirectory within the project to scope the listing to (defaults to base_dir)."
                }
            },
            "required": [],
            "additionalProperties": False
        }
    }
}
