import os
import tempfile
from datetime import datetime
from difflib import unified_diff
from pathlib import Path

from codey.utils import assert_within_project


def _atomic_write(target: Path, content: str) -> None:
    """Write `content` to `target` atomically via tempfile + os.replace."""
    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".codey_", dir=str(parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_name, target)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def edit_file(
    filename: str,
    content: str,
    base_dir: str = None,
    create_backup: bool = True,
) -> str:
    """
    Completely replace a file's content.

    Writes atomically and, by default, saves a timestamped backup
    (filename.bak.YYYYMMDDHHMMSS) before replacing. Computes the diff
    using difflib.unified_diff so the result is deterministic and does
    not depend on the git state of the working tree.
    """
    if base_dir is None:
        base_dir = os.getcwd()
    base_path = Path(base_dir).resolve()
    target = (base_path / filename).resolve() if not os.path.isabs(filename) else Path(filename).resolve()

    try:
        assert_within_project(str(target), str(base_path))
    except ValueError as e:
        return f"Error: {e}"

    if not target.is_file():
        return f"Error: File '{filename}' not found."

    try:
        old_content = target.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading '{filename}': {e}"

    backup_path = None
    if create_backup:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = target.with_suffix(target.suffix + f".bak.{ts}")
        try:
            backup_path.write_text(old_content, encoding="utf-8")
        except Exception as e:
            return f"Error creating backup for '{filename}': {e}"

    try:
        _atomic_write(target, content)
    except Exception as e:
        return f"Error writing '{filename}': {e}"

    diff = "\n".join(
        unified_diff(
            old_content.splitlines(keepends=True),
            content.splitlines(keepends=True),
            fromfile=f"{filename} (before)",
            tofile=f"{filename} (after)",
            n=3,
        )
    )
    summary = {
        "updated": True,
        "path": str(target),
        "backup": str(backup_path) if backup_path else None,
        "diff_lines": diff.count("\n") + (1 if diff else 0),
        "size_before": len(old_content),
        "size_after": len(content),
    }
    return f"File '{filename}' updated.\n\n{diff}\n[structured] {summary}"


schema = {
    "type": "function",
    "function": {
        "name": "edit_file",
        "description": (
            "Replace entire file content. First read the file with read_files, "
            "then write back the complete modified content. Writes atomically and "
            "creates a timestamped backup (filename.bak.YYYYMMDDHHMMSS) by default. "
            "Diff is computed with difflib.unified_diff, so no git state is required. "
            "Pass create_backup=False to skip the backup. Returns a structured summary."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Path of the file to edit (relative to base_dir or absolute)."
                },
                "content": {
                    "type": "string",
                    "description": "Complete new file content."
                },
                "create_backup": {
                    "type": "boolean",
                    "description": "Whether to save a timestamped .bak file before writing. Defaults to true.",
                    "default": True
                }
            },
            "required": ["filename", "content"],
            "additionalProperties": False
        }
    }
}