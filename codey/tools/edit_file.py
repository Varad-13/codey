import os
import subprocess
from codey.utils import assert_within_project


def edit_file(filename: str, content: str) -> str:
    """
    Completely replace a file's content.

    Returns git diff showing the changes.
    """
    base_dir = os.getcwd()
    filepath = filename if os.path.isabs(filename) else os.path.join(base_dir, filename)

    try:
        assert_within_project(filepath, base_dir)
    except ValueError as e:
        return f"Error: {e}"

    if not os.path.isfile(filepath):
        return f"Error: File '{filename}' not found."

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        proc = subprocess.run(
            ["git", "diff", filepath],
            capture_output=True,
            text=True,
            cwd=base_dir,
        )
        diff_output = proc.stdout + proc.stderr
        return f"File '{filename}' updated.\n\n{diff_output}"

    except Exception as e:
        return f"Error: {e}"


schema = {
    "type": "function",
    "function": {
        "name": "edit_file",
        "description": "Replace entire file content. First read the file with read_files, then write back the complete modified content.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Path to the file."
                },
                "content": {
                    "type": "string",
                    "description": "Complete new file content."
                }
            },
            "required": ["filename", "content"]
        }
    }
}
