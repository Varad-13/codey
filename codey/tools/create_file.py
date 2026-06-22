import os
import stat
import tempfile
from pathlib import Path

from codey.utils import assert_within_project

DEFAULT_MODE = 0o644
EXECUTABLE_MODE = 0o755


def _atomic_write(target: Path, content: str) -> None:
    """Write `content` to `target` atomically via tempfile + os.replace.

    Avoids leaving a partial file on disk if the process is interrupted.
    """
    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".codey_", dir=str(parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_name, target)
    except Exception:
        # Clean up the temp file on any failure
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def create_file(
    filename: str,
    content: str,
    base_dir: str = None,
    overwrite: bool = True,
    make_executable: bool = False,
) -> str:
    """
    Create a new text file with the given content.

    Ensures any parent directories exist. Writes atomically (via tempfile +
    os.replace) to avoid partial writes. Default file mode is 0o644; pass
    make_executable=True to set 0o755 instead. By default the file is
    overwritten if it already exists; pass overwrite=False to refuse
    instead. Returns a structured summary including the final path, mode,
    and content preview.
    """
    if base_dir is None:
        base_dir = os.getcwd()
    base_path = Path(base_dir).resolve()
    target = (base_path / filename).resolve()

    try:
        assert_within_project(str(target), str(base_path))
    except ValueError as e:
        return f"Error: {e}"

    existed = target.exists()
    if existed and not overwrite:
        return (
            f"Error: '{filename}' already exists and overwrite=False. "
            "Pass overwrite=True to replace, or choose a different filename."
        )

    try:
        _atomic_write(target, content)
        mode = EXECUTABLE_MODE if make_executable else DEFAULT_MODE
        # Preserve existing executable bit if user didn't explicitly ask
        if existed and not make_executable:
            try:
                old_mode = target.stat().st_mode
                if old_mode & stat.S_IXUSR:
                    mode = old_mode
            except OSError:
                pass
        os.chmod(target, mode)

        preview = content if len(content) <= 400 else content[:400] + "..."
        summary = {
            "created": not existed,
            "overwritten": existed,
            "path": str(target),
            "mode": mode,
            "content_preview": preview,
        }
        verb = "Updated" if existed else "Created"
        return f"{verb} '{filename}' (mode={oct(mode)}).\n[structured] {summary}"
    except Exception as e:
        return f"Error creating {filename}: {e}"


schema = {
    "type": "function",
    "function": {
        "name": "create_file",
        "description": (
            "Create or overwrite a text file (and any parent dirs) with given content. "
            "Writes atomically (tempfile + os.replace) so partial writes never reach disk. "
            "Default file mode is 0o644; pass make_executable=True for 0o755. "
            "Pass overwrite=False to refuse if the file already exists. "
            "Returns a structured summary with the final path, mode, and content preview."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Path of the file to create (relative to base_dir or absolute)."},
                "content": {"type": "string", "description": "Full file contents to write."},
                "overwrite": {"type": "boolean", "description": "Whether to overwrite an existing file. Defaults to true.", "default": True},
                "make_executable": {"type": "boolean", "description": "If true, set file mode to 0o755 instead of 0o644. Defaults to false.", "default": False}
            },
            "required": ["filename", "content"],
            "additionalProperties": False
        }
    }
}