# tools/shell.py

import subprocess

def shell(command: str) -> str:
    """
    Run a shell/PowerShell command (non-interactive).
    """
    proc = subprocess.run(
        ["powershell", "-Command", command],
        capture_output=True,
        text=True,
    )
    out = proc.stdout + proc.stderr
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
