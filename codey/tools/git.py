import subprocess


def run_git_command(command: str):
    """Run a git command with arbitrary args and return output or error."""
    try:
        result = subprocess.run(
            ['git'] + command.split(), 
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Git command error: {e.stderr.strip()}"


def git_command_handler(params: dict):
    command = params.get('command')
    if not command:
        return "Error: 'command' argument is required for git tool."
    return run_git_command(command)


# Additional git stash commands

def git_stash_handler(params: dict):
    command = params.get('command')
    if not command:
        return "Error: 'command' argument is required for git stash tool."
    full_command = f"stash {command}"
    return run_git_command(full_command)

# Schema and documentation updated accordingly
schema = {
    "name": "git",
    "description": "Run arbitrary git commands. Provide full git command arguments as a single string. For example, 'status', 'checkout branch-name', 'commit -m \"message\"'.",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Full git command arguments as single string."
            },
        },
        "required": ["command"],
    },
}

stash_schema = {
    "name": "git_stash",
    "description": "Run git stash commands. Provide stash command arguments as a single string, e.g. 'save', 'pop', 'list', 'apply', 'drop stash@{0}'.",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Arguments for git stash command."
            }
        },
        "required": ["command"],
    },
}

# Export handlers for integration

handlers = {
    'git': git_command_handler,
    'git_stash': git_stash_handler,
}
