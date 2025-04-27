from codestorm.tools.shell import shell

class GitTool:
    def __init__(self):
        pass

    def add(self, files=None):
        if files:
            return shell(f'git add {files}')  # Add specified files
        return shell('git add -A')  # Add all files if none specified

    def commit(self, message):
        return shell(f'git commit -m "{message}"')  # Message only matters for commit

    def diff(self):
        return shell('git diff')

    def status(self):
        return shell('git status')

    def log(self):
        return shell('git log')

    def checkout(self, branch):
        return shell(f'git checkout {branch}')  # Branch only matters for checkout

    def rm(self, files):
        return shell(f'git rm {files}')  # Files required for rm command

schema = {
    "type": "function",
    "name": "git_tool",
    "description": "A tool to handle Git functionality. The commands and their relevant parameters are as follows: \n- `add`: Add files to the staging area. Specify files to add certain files or omit for all.\n- `commit`: Commit staged changes with a message. The message is mandatory.\n- `diff`: Show unstaged changes. No additional parameters required.\n- `status`: Display the working directory status.\n- `log`: Show commit history.\n- `checkout`: Switch to a specified branch. The branch parameter is necessary.\n- `rm`: Remove files from the staging area. Requires the names of files to be removed.\n","parameters": {
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
            "files": {"type": "string"}
        },
        "required": ["command"],
        "additionalProperties": False
    }
}