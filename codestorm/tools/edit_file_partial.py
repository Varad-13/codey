import os

def edit_file_partial(filename: str, mode: str, start_line: int, end_line: int, content: str = "") -> str:
    """
    Partially edit a file.
    Modes:
      - insert: insert `content` at line start_line
      - delete: delete lines from start_line to end_line inclusive
    Returns updated file content or error.
    """
    if not os.path.isfile(filename):
        return f"Error: File '{filename}' not found."

    if mode not in ("insert", "delete"):
        return f"Error: mode must be 'insert' or 'delete'."

    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if start_line < 1 or end_line > len(lines) or start_line > end_line:
            return f"Error: invalid line range {start_line} to {end_line} for file with {len(lines)} lines."

        if mode == "delete":
            # remove lines from start_line to end_line (1-based indexing)
            del lines[start_line - 1:end_line]
        elif mode == "insert":
            # insert content lines at start_line (before that line)
            content_lines = content.splitlines(keepends=True)
            insert_pos = start_line - 1
            lines = lines[:insert_pos] + content_lines + lines[insert_pos:]

        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(lines)

        with open(filename, "r", encoding="utf-8") as f:
            return f.read()

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
        "required": ["filename", "mode", "start_line", "end_line"],
        "additionalProperties": False
    }
}
