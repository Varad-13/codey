from codestorm.tools.shell import shell

class Git:
    def __init__(self):
        pass

    def add(self, files=None, args=None):
        if args:
            return shell(f'git add {args} {files}')  # Add specified files with any extra args
        if files:
            return shell(f'git add {files}')  # Add specified files
        return shell('git add -A')  # Add all files if none specified

    def commit(self, message, args=None):
        message = f"{message}+\n\n - Signed off by Codey"
        if args:
            return shell(f'git commit {args} -m "{message}"')  # Message only matters for commit
        return shell(f'git commit -m "{message}"')  # Message only matters for commit

    def diff(self, args=None):
        if args:
            return shell(f'git diff {args}')  # Show unstaged changes with additional args
        return shell('git diff')

    def status(self, args=None):
        if args:
            return shell(f'git status {args}')  # Display status with additional args
        return shell('git status')

    def log(self, args=None):
        if args:
            return shell(f'git log {args}')  # Show commit history with additional args
        return shell('git log')

    def checkout(self, branch, args=None):
        if args:
            return shell(f'git checkout {args} {branch}')  # Branch with additional args
        return shell(f'git checkout {branch}')  # Branch only matters for checkout

    def branch(self, args=None):
        """
        List branches or create/delete branches based on args.
        """
        if args:
            return shell(f'git branch {args}')  # Additional args for branch command
        return shell('git branch')  # List branches by default

    def rm(self, files, args=None):
        if args:
            return shell(f'git rm {args} {files}')  # Files required for rm command with additional args
        return shell(f'git rm {files}')  # Files required for rm command

    def __call__(self, command, message=None, branch=None, files=None, args=None):
        """
        Make the Git tool instance callable, routing to the appropriate method.
        """
        # Map command to method
        if not hasattr(self, command):
            raise ValueError(f"Unknown git command: {command}")
        method = getattr(self, command)
        # Prepare kwargs for the method, include only non-None
        kwargs = {}
        if command == 'commit':
            kwargs['message'] = message
        if command == 'checkout':
            kwargs['branch'] = branch
        if command in ('add', 'rm'):
            kwargs['files'] = files
        # Common optional args param
        if args is not None:
            kwargs['args'] = args
        return method(**kwargs)

schema = {
    "type": "function",
    "name": "git",
    "description": (
        "A tool to handle Git functionality. The commands and their relevant parameters are as follows:\n"
        "- `add`: Add files to the staging area. Specify files to add certain files or omit for all. You can also provide additional arguments.\n"
        "- `commit`: Commit staged changes with a message. Commit messages must follow the format: `type: subject` (<=50 chars), blank line, optional detailed body. Types: feat, fix, docs, style, refactor, test, chore."
        "- `diff`: Show unstaged changes. Can include additional arguments.\n"
        "- `status`: Display the working directory status. Additional arguments can be supplied.\n"
        "- `log`: Show commit history. Additional arguments can be included.\n"
        "- `checkout`: Switch to a specified branch. The branch parameter is necessary and can be followed by additional arguments.\n"
        "- `branch`: List, create, or delete branches based on provided arguments.\n"
        "- `rm`: Remove files from the staging area. Requires the names of files to be removed and can include additional arguments."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "enum": [
                    "add",
                    "commit",
                    "diff",
                    "status",
                    "log",
                    "checkout",
                    "branch",
                    "rm"
                ]
            },
            "message": {"type": "string"},
            "branch": {"type": "string"},
            "files": {"type": "string"},
            "args": {"type": "string"}
        },
        "required": ["command"],
        "additionalProperties": False
    }
}