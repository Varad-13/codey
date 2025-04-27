import os
from codey.tools.shell import shell

def edit_file(filename: str, content: str) -> str:
    """
    Replace the full content of an existing file.
    Returns success message or error message and git diff output.
    """
    if not os.path.isfile(filename):
        return f"Error: File '{filename}' not found."
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        diff_output = shell("git diff")
        return "File edited successfully." + "\n" + diff_output
    except Exception as e:
        return f"Error updating {filename}: {e}"

schema = {
    "type": "function",
    "name": "edit_file",
    "description": "Replace the full content of an existing file.",
    "parameters": {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "content": {"type": "string"}
        },
        "required": ["filename", "content"],
        "additionalProperties": False
    }
}
schema = {
    "type": "function",
    "name": "edit_file",
    "description": "Replace the full content of an existing file.",
    "parameters": {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "content": {"type": "string"}
        },
        "required": ["filename", "content"],
        "additionalProperties": False
    }
}
