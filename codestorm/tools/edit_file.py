import os

def edit_file(filename: str, content: str) -> str:
    """
    Replace the full content of an existing file.
    Returns success message or error message.
    """
    if not os.path.isfile(filename):
        return f"Error: File '{filename}' not found."
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return "File edited successfully."
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
