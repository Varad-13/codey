import os
from pathlib import Path
from codey.utils import assert_within_project

# 1 MB per-file size limit. Larger files get a snippet + message.
MAX_FILE_SIZE = 1 * 1024 * 1024
# How many bytes to inspect when deciding whether a file is binary.
BINARY_SCAN_BYTES = 8192
# Snippet length when a file exceeds the size limit.
SNIPPET_BYTES = 4096


def _looks_binary(head_bytes: bytes) -> bool:
    """Heuristic: treat files containing null bytes in the head as binary."""
    return b"\x00" in head_bytes


def read_files(file_list: str, base_dir: str = None) -> str:
    """
    Read one or more files given a comma-separated list of filenames.
    Returns each file's content numbered by line for easier analysis.

    Files larger than 1 MB return a snippet + a clear notice instead of full
    contents. Files detected as binary (null bytes in first 8 KB) are skipped
    with a clear "binary file skipped" message.
    """
    if base_dir is None:
        base_dir = os.getcwd()
    base_path = Path(base_dir).resolve()

    outputs = []
    for fname in [f.strip() for f in file_list.split(",")]:
        if not fname:
            continue
        target = (base_path / fname).resolve()
        try:
            assert_within_project(str(target), str(base_path))
        except ValueError:
            outputs.append(f"**Error:** '{fname}' is outside the project directory.")
            continue

        if not target.is_file():
            outputs.append(f"**Error:** '{fname}' not found.")
            continue

        try:
            size = target.stat().st_size
            if size > MAX_FILE_SIZE:
                with open(target, "rb") as fh:
                    snippet = fh.read(SNIPPET_BYTES)
                outputs.append(
                    f"----- {fname} ----- (file is {size} bytes; > {MAX_FILE_SIZE} byte limit; "
                    f"showing first {SNIPPET_BYTES} bytes)\n{snippet!r}"
                )
                continue

            with open(target, "rb") as fh:
                head = fh.read(BINARY_SCAN_BYTES)
            if _looks_binary(head):
                outputs.append(f"----- {fname} ----- (binary file skipped; {size} bytes)")
                continue

            with open(target, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
            numbered_lines = [f"{i+1}: {line.rstrip()}" for i, line in enumerate(lines)]
            outputs.append(f"----- {fname} -----\n" + "\n".join(numbered_lines))
        except Exception as e:
            outputs.append(f"**Error reading {fname}:** {e}")
    return "\n\n".join(outputs)


schema = {
    "type": "function",
    "function": {
        "name": "read_files",
        "description": "Read files by comma-separated list, returning numbered lines for each file. Files larger than 1 MB return a snippet instead of full content; binary files (null bytes in first 8 KB) are skipped with a notice.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_list": {
                    "type": "string",
                    "description": "Comma-separated list of file paths to read."
                },
                "base_dir": {
                    "type": "string",
                    "description": "Project root directory (defaults to current working directory)."
                }
            },
            "required": ["file_list"],
            "additionalProperties": False
        }
    }
}
