import os
from codestorm.tools.shell import shell

def edit_files_by_string(file_list: str, search_string: str, replace_string: str) -> str:
    """
    Search and replace across multiple files given by comma-separated file_list.
    Use only if no user error is reported. For errors, prefer a full rewrite with edit_file.
    Returns a summary of changes and git diff output.
    """
    base_dir = os.getcwd()
    results = []
    files = [f.strip() for f in file_list.split(",")]

    for fname in files:
        filepath = os.path.join(base_dir, fname)
        if not os.path.isfile(filepath):
            results.append(f"**Error:** '{fname}' not found.")
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if search_string not in content:
                results.append(f"'{fname}': search string not found.")
                continue

            updated_content = content.replace(search_string, replace_string)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(updated_content)

            results.append(f"'{fname}': replaced occurrences.")

        except Exception as e:
            results.append(f"Error processing {fname}: {e}")

    diff_output = shell("git diff")
    return "\n".join(results) + "\n" + diff_output

schema = {
    "type": "function",
    "name": "edit_files_by_string",
    "description": "Search and replace a string across multiple files (case-sensitive). Only use if user does not report errors; for errors, prefer full file rewrite.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_list": {"type": "string"},
            "search_string": {"type": "string"},
            "replace_string": {"type": "string"}
        },
        "required": ["file_list", "search_string", "replace_string"],
        "additionalProperties": False
    }
}
schema = {
    "type": "function",
    "name": "edit_files_by_string",
    "description": "Search and replace a string across multiple files (case-sensitive). Only use if user does not report errors; for errors, prefer full file rewrite.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_list": {"type": "string"},
            "search_string": {"type": "string"},
            "replace_string": {"type": "string"}
        },
        "required": ["file_list", "search_string", "replace_string"],
        "additionalProperties": False
    }
}
