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
                    "branch"
                ]
            },
            "message": {"type": "string"},
            "branch": {"type": "string"}
        },
        "required": ["command"],
        "additionalProperties": False
    }
}