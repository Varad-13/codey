import os
import difflib
from codey.tools.shell import shell

def edit_files_by_string(file_list: str, search_string: str, replace_string: str, apply: bool = False) -> str:
    """
    Search and replace a string across multiple files (case-sensitive).
    For large refactors only. By default (apply=False), performs a dry-run and returns unified diffs.
    If apply=True, writes changes to files and returns git diff output.

    Parameters:
    - file_list: comma-separated file paths relative to cwd.
    - search_string: substring to search for.
    - replace_string: string to replace occurrences with.
    - apply: if True, apply changes; if False, only show diffs without writing.
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
                original = f.read().splitlines(keepends=True)

            if search_string not in "".join(original):
                results.append(f"'{fname}': search string not found.")
                continue

            updated = [line.replace(search_string, replace_string) for line in original]

            if apply:
                # Write changes
                with open(filepath, "w", encoding="utf-8") as f:
                    f.writelines(updated)
                # Rely on git diff for applied changes
                diff_output = shell("git diff")
                results.append(f"'{fname}': applied replacements.")
                results.append(diff_output)
            else:
                # Generate unified diff for preview
                diff = difflib.unified_diff(
                    original,
                    updated,
                    fromfile=f"a/{fname}",
                    tofile=f"b/{fname}",
                    lineterm=""
                )
                preview = "\n".join(diff)
                results.append(f"Preview diff for '{fname}':")
                results.append(preview if preview else "(no changes)" )

        except Exception as e:
            results.append(f"Error processing {fname}: {e}")

    return "\n".join(results)

schema = {
    "type": "function",
    "name": "edit_files_by_string",
    "description": (
        "Search and replace a string across multiple files (case-sensitive). "
        "Intended for large refactors. By default (apply=False) returns a preview unified diff; "
        "with apply=True writes changes and returns git diff."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "file_list": {"type": "string", "description": "Comma-separated file paths to process."},
            "search_string": {"type": "string", "description": "Substring to search for in files."},
            "replace_string": {"type": "string", "description": "Replacement string."},
            "apply": {"type": "boolean", "description": "If true, apply changes; otherwise only preview diffs."}
        },
        "required": ["file_list", "search_string", "replace_string"],
        "additionalProperties": False
    }
}