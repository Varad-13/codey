import os
from codey.utils import assert_within_project


def create_file(filename: str, content: str) -> str:
    """
    Create a new text file with the given content.
    Ensures any parent directories exist.
    Returns the file's content or an error message.
    """
    base_dir = os.getcwd()
    filepath = os.path.join(base_dir, filename)

    try:
        assert_within_project(filepath, base_dir)
    except ValueError as e:
        return f"Error: {e}"

    parent = os.path.dirname(filepath)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
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
