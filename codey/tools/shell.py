import os
import subprocess
import sys


def shell(command: str) -> str:
    """
    Run a shell command (non-interactive) in the user's current working directory.
    Uses PowerShell on Windows, /bin/sh on Unix-like systems.
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

    out = proc.stdout + proc.stderr
    return f"Command `{command}` exited with code {proc.returncode}:\n{out}"


schema = {
    "type": "function",
    "function": {
        "name": "shell",
        "description": "Run a shell/PowerShell command, non-interactive.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"}
            },
            "required": ["command"]
        }
    }
}
