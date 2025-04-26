import os
from codestorm.tools.shell import shell
import os


def edit_file_partial(filename: str, mode: str, start_line: int, end_line: int = None, content: str = "") -> str:
    """
    Partially edit a file.
    Modes:
      - insert: insert `content` at line start_line, pushing existing lines down without overwriting
      - delete: delete lines from start_line to end_line inclusive
      - replace: replace lines from start_line to end_line with `content`
    Use partial edits only for incremental changes when user has not reported errors. For major fixes after errors, prefer full file rewrite.
    Returns success message or error message.
    """
    if not os.path.isfile(filename):
        return f"Error: File '{filename}' not found."

    if mode not in ("insert", "delete", "replace"):
        return f"Error: mode must be 'insert', 'delete', or 'replace'."

    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()

        file_line_count = len(lines)

        # Validate line ranges and sanity checks
        if start_line < 1 or start_line > file_line_count + 1:
            return f"Error: invalid start_line {start_line} for file with {file_line_count} lines."

        if mode == "delete" or mode == "replace":
            if end_line is None:
                return f"Error: end_line is required for {mode} mode."
            if end_line < start_line:
                return f"Error: end_line {end_line} is less than start_line {start_line}."
            if end_line > file_line_count:
                return f"Error: end_line {end_line} is beyond end of file with {file_line_count} lines."

            # Optional: limit maximum number of lines to delete/replace to avoid huge edits
            max_edit_lines = 1000
            if (end_line - start_line + 1) > max_edit_lines:
                return f"Error: too many lines to {mode} ({end_line - start_line + 1} lines), exceeds limit of {max_edit_lines}."

        # Insert mode: insert new lines at start_line position
        if mode == "insert":
            content_lines = content.splitlines(keepends=True)
            # Insert position is start_line - 1 (0-indexed)
            insert_pos = start_line - 1
            lines = lines[:insert_pos] + content_lines + lines[insert_pos:]

        elif mode == "delete":
            del lines[start_line - 1:end_line]

        elif mode == "replace":
            content_lines = content.splitlines(keepends=True)
            lines = lines[:start_line - 1] + content_lines + lines[end_line:]

        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return "File edited successfully."

    except Exception as e:
        return f"Error editing {filename}: {e}"
schema = {
    "type": "function",
    "name": "edit_file_partial",
    "description": "Partially edit a file by insert, delete or replace mode on specified line range. Only use for incremental changes, avoid partial edits if user reported errors; prefer full rewrite then.",
    "parameters": {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "mode": {"type": "string", "enum": ["insert", "delete", "replace"]},
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
    },
    "allOf": [
        {
            "if": {"properties": {"mode": {"const": "replace"}}},
            "then": {"required": ["end_line"]}
        }
    ]
}
