from codestorm.tools.shell import shell

class GitTool:
    def __init__(self):
        pass

    def add(self):
        return shell('git add -A')

    def commit(self, message):
        return shell(f'git commit -m "{message}"')

    def diff(self):
        return shell('git diff')

    def status(self):
        return shell('git status')

    def log(self):
        return shell('git log')

    def checkout(self, branch):
        return shell(f'git checkout {branch}')

    def branch(self):
        return shell('git branch')

    def rm(self, files):
        return shell(f'git rm {files}')

schema = {
    "type": "function",
    "name": "git_tool",
    "description": "A tool to handle Git functionality.",
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
            "files": {"type": "string"}
        },
        "required": ["command"],
        "additionalProperties": False
    }
}