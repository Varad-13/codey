import os
import shlex
import subprocess
import sys


class Git:
    """Stateless Git tool: run whitelisted git commands with appended args."""

    ALLOWED = [
        "add", "commit", "diff", "status", "log",
        "checkout", "branch", "rm", "merge", "stash",
        "reset", "revert"
    ]

    def __call__(self, command, args=None):
        if command not in self.ALLOWED:
            raise ValueError(f"Unknown git command: {command}")
        cmd = ["git", command]
        if args:
            # posix=False on Windows so backslashes in paths are not treated as escapes
            cmd += shlex.split(args, posix=(sys.platform != "win32"))
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        out = proc.stdout + proc.stderr
        return f"Command `git {command}` exited with code {proc.returncode}:\n{out}"


schema = {
    "type": "function",
    "function": {
        "name": "git",
        "description": (
            "Run an atomic, stateless git command. "
            "Whitelisted commands: " + ", ".join(Git.ALLOWED) + ". "
            "Provide any additional git arguments or targets as a single string via 'args'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": Git.ALLOWED,
                    "description": "Git subcommand to execute."
                },
                "args": {
                    "type": "string",
                    "description": "Optional arguments or targets to append to the git subcommand."
                }
            },
            "required": ["command"],
            "additionalProperties": False
        }
    }
}
