# tools/create_file.py

import os

def create_file(filename: str, content: str) -> str:
    """
    Create a new text file with the given content.
    Ensures any parent directories exist and sets executable permissions.
    Returns the file’s content or an error message.
    """
    parent = os.path.dirname(filename)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(filename, 0o755)
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error creating {filename}: {e}"

schema = {
    "type": "function",
    "name": "create_file",
    "description": "Create a new text file (and any parent dirs) with given content.",
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
