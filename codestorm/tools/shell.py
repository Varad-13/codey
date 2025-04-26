import subprocess
import os
import sys

def shell(command: str) -> str:
    """
    Run a shell command (non-interactive) in user's current working directory.
    Uses PowerShell on Windows, `/bin/sh` on Unix-like systems.
    """
    base_dir = os.getcwd()

    if sys.platform.startswith("win"):
        shell_cmd = ["powershell", "-Command", command]
    else:
        shell_cmd = ["/bin/sh", "-c", command]

    proc = subprocess.run(
        shell_cmd,
        capture_output=True,
        text=True,
        cwd=base_dir,
    )

    out = str(proc.stdout) + str(proc.stderr)
    if proc.returncode == 0 and not out:
        return f"Command `{command}` executed successfully."
    return out

schema = {
    "type": "function",
    "name": "shell",
    "description": "Run a shell/PowerShell command, non-interactive.",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {"type": "string"}
        },
        "required": ["command"],
        "additionalProperties": False
    }
}
