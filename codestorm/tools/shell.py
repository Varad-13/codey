import subprocess
import os

def shell(command: str) -> str:
    """
    Run a shell/PowerShell command (non-interactive) in user's current working directory.
    """
    # Use os.getcwd() as the base directory
    base_dir = os.getcwd()
    proc = subprocess.run(
        ["powershell", "-Command", command],
        capture_output=True,
        text=True,
        cwd=base_dir,
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
