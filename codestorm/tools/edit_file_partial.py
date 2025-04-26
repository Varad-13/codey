import os
from codestorm.tools.shell import shell

def edit_file_partial(filename: str, mode: str, start_line: int, end_line: int = None, content: str = "") -> str:
    """
    Partially edit a file.
    Modes:
      - insert: insert `content` at line start_line
      - delete: delete lines from start_line to end_line inclusive
      - replace: replace lines from start_line to end_line with `content`
    Use partial edits only for incremental changes when user has not reported errors. For major fixes after errors, prefer full file rewrite.
    Returns success message or error message and git diff output.
    """
    if not os.path.isfile(filename):
        return f"Error: File '{filename}' not found."

    if mode not in ("insert", "delete", "replace"):
        return f"Error: mode must be 'insert', 'delete', or 'replace'."

    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if mode == "delete":
            if end_line is None:
                return f"Error: end_line is required for delete mode."
            if start_line < 1 or end_line > len(lines) or start_line > end_line:
                return f"Error: invalid line range {start_line} to {end_line} for file with {len(lines)} lines."
            del lines[start_line - 1:end_line]

        elif mode == "insert":
            if start_line < 1 or start_line > len(lines) + 1:
                return f"Error: invalid start_line {start_line} for insert in file with {len(lines)} lines."
            content_lines = content.splitlines(keepends=True)
            insert_pos = start_line - 1
            lines = lines[:insert_pos] + content_lines + lines[insert_pos:]

        elif mode == "replace":
            if end_line is None:
                return f"Error: end_line is required for replace mode."
            if start_line < 1 or end_line > len(lines) or start_line > end_line:
                return f"Error: invalid line range {start_line} to {end_line} for file with {len(lines)} lines."
            content_lines = content.splitlines(keepends=True)
            lines = lines[:start_line - 1] + content_lines + lines[end_line:]

        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(lines)

        diff_output = shell("git diff")
        return "File edited successfully." + "\n" + diff_output

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
