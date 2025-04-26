import os

def edit_file_partial(filename: str, mode: str, start_line: int, end_line: int = None, content: str = "") -> str:
    """
    Partially edit a file.
    Modes:
      - insert: insert `content` at line start_line
      - delete: delete lines from start_line to end_line inclusive
    Returns success message or error message.
    """
    if not os.path.isfile(filename):
        return f"Error: File '{filename}' not found."

    if mode not in ("insert", "delete"):
        return f"Error: mode must be 'insert' or 'delete'."

    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if mode == "delete":
            if end_line is None:
                return f"Error: end_line is required for delete mode."
            if start_line < 1 or end_line > len(lines) or start_line > end_line:
                return f"Error: invalid line range {start_line} to {end_line} for file with {len(lines)} lines."
            # remove lines from start_line to end_line (1-based indexing)
            del lines[start_line - 1:end_line]

        elif mode == "insert":
            if start_line < 1 or start_line > len(lines) + 1:
                return f"Error: invalid start_line {start_line} for insert in file with {len(lines)} lines."
            content_lines = content.splitlines(keepends=True)
            insert_pos = start_line - 1
            lines = lines[:insert_pos] + content_lines + lines[insert_pos:]

        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return "File edited successfully."

    except Exception as e:
        return f"Error editing {filename}: {e}"

schema = {
    "type": "function",
    "name": "edit_file_partial",
    "description": "Partially edit a file by insert or delete mode on specified line range.",
    "parameters": {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "mode": {"type": "string", "enum": ["insert", "delete"]},
            "start_line": {"type": "integer"},
            "end_line": {"type": "integer"},
            "content": {"type": "string"}
        },
        "required": ["filename", "mode", "start_line"],
        "additionalProperties": False
    },
    "if": {
        "properties": {"mode": {"const": "delete"}},
        "required": ["end_line"]
    }
}
