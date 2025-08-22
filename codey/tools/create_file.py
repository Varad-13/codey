import os

def create_file(filename: str, content: str) -> str:
    """
    Create a new text file with the given content.
    Ensures any parent directories exist and sets executable permissions.
    Returns the file's content or an error message.
    """
    base_dir = os.getcwd()
    # Make the filename absolute based on base_dir
    filepath = os.path.join(base_dir, filename)
    parent = os.path.dirname(filepath)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(filepath, 0o755)
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error creating {filename}: {e}"

schema = {
    "type": "function",
    "function": {
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
}
