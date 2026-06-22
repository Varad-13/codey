import os
import subprocess
import sys

DEFAULT_TIMEOUT = 30  # seconds


def shell(command: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """
    Run a shell command (non-interactive) in the user's current working directory.
    Uses PowerShell on Windows, /bin/sh on Unix-like systems.

    WARNING: This tool can execute arbitrary commands, including destructive ones
    (rm, git push --force, drop tables, etc.). Always review the command before
    approving and prefer the more targeted tools (git, edit_file, create_file)
    when possible. A 30-second timeout is enforced by default; pass timeout=N
    to override.
    """
    base_dir = os.getcwd()

    if sys.platform.startswith("win"):
        shell_cmd = ["powershell", "-Command", command]
    else:
        shell_cmd = ["/bin/sh", "-c", command]

    try:
        proc = subprocess.run(
            shell_cmd,
            capture_output=True,
            text=True,
            cwd=base_dir,
            timeout=timeout,
            check=False,
        )
        out = proc.stdout + proc.stderr
        return f"Command `{command}` exited with code {proc.returncode}:\n{out}"
    except subprocess.TimeoutExpired:
        return f"Error: command `{command}` timed out after {timeout} seconds."
    except FileNotFoundError as e:
        return f"Error: shell interpreter not found ({e})."
    except Exception as e:
        return f"Error executing `{command}`: {e}"


schema = {
    "type": "function",
    "function": {
        "name": "shell",
        "description": (
            "Run a shell/PowerShell command (non-interactive) in the current working directory. "
            "WARNING: can execute arbitrary commands including destructive ones (rm, force-push, "
            "drop tables, etc.). Review commands carefully before approving. A 30-second timeout "
            "is enforced by default; pass timeout=N to override."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute."},
                "timeout": {
                    "type": "integer",
                    "description": "Maximum execution time in seconds (default 30).",
                    "default": DEFAULT_TIMEOUT,
                    "minimum": 1,
                },
            },
            "required": ["command"],
            "additionalProperties": False,
        },
    },
}