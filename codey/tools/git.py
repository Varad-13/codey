from codey.tools.shell import shell

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
        cmd = f"git {command}"
        if args:
            cmd += f" {args}"
        return shell(cmd)

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
