import os

def edit_file(filename: str, content: str) -> str:
    """
    Replace the full content of an existing file.
    Returns the updated file content or an error message.
    """
    base_dir = os.getcwd()
    filepath = os.path.join(base_dir, filename)
    if not os.path.isfile(filepath):
        return f"Error: File '{filename}' not found."
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
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
