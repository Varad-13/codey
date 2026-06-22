import os
import subprocess
import tempfile

from codey.utils import assert_within_project


VALID_MODES = ("find_replace", "replace_range", "insert")


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _split_lines(text: str):
    """Return (lines_without_terminators, had_trailing_newline).

    Empty file -> ([], False). A file ending with '\n' -> splitlines() drops the
    terminator but still includes the trailing line, so we report had_trailing_nl=True
    so the writer can re-add it.
    """
    if text == "":
        return [], False
    trailing = text.endswith("\n")
    return text.splitlines(), trailing


def _split_content_lines(content: str):
    """Split user-supplied content into lines, dropping a trailing empty element
    that would otherwise be produced by a final '\n'.
    """
    if content == "":
        return []
    parts = content.split("\n")
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return parts


def _write_atomic(path: str, text: str) -> None:
    """Write text to path via tempfile.mkstemp + os.replace.

    On any failure the partial temp file is cleaned up so the original is left
    intact. No .bak files are written — git history is the undo log.
    """
    parent = os.path.dirname(path) or "."
    fd, tmp_name = tempfile.mkstemp(prefix=".codey_edit_", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _git_diff(filepath: str, base_dir: str) -> str:
    try:
        proc = subprocess.run(
            ["git", "diff", filepath],
            capture_output=True,
            text=True,
            cwd=base_dir,
        )
        return proc.stdout + proc.stderr
    except FileNotFoundError:
        return "(git not available; skipping diff preview)"
    except Exception as e:
        return f"(git diff failed: {e})"


def _rejoin(lines, had_trailing_newline: bool) -> str:
    text = "\n".join(lines)
    if had_trailing_newline and text != "":
        text += "\n"
    return text


def edit_file(
    filename: str,
    mode: str,
    *,
    search_text: str = None,
    replacement: str = None,
    replace_all: bool = False,
    start_line: int = None,
    end_line: int = None,
    line: int = None,
    content: str = None,
) -> str:
    """Surgical file editor with three modes.

    Modes (pick ONE per call):
      - "find_replace": exact-string find/replace. Use when the snippet is unique
        and you don't want to count lines. Pass search_text, replacement, and
        optionally replace_all=True.
      - "replace_range": replace lines [start_line, end_line] (1-indexed, inclusive)
        with replacement. Use when the change spans a known line range.
      - "insert": insert content after `line` (0 = top of file, total = end of file).
        Use when adding new lines without disturbing existing ones.

    For full-file rewrites, use create_file with overwrite=True instead.
    Returns a short summary plus the unified diff from `git diff`. On error
    returns a clear, actionable message (no stack traces).
    """
    if mode not in VALID_MODES:
        return (
            f"Error: Invalid mode '{mode}'. "
            f"Must be one of: {', '.join(VALID_MODES)}."
        )

    base_dir = os.getcwd()
    filepath = filename if os.path.isabs(filename) else os.path.join(base_dir, filename)

    try:
        assert_within_project(filepath, base_dir)
    except ValueError as e:
        return f"Error: {e}"

    if not os.path.isfile(filepath):
        return f"Error: File '{filename}' not found."

    try:
        raw = _read_text(filepath)
    except Exception as e:
        return f"Error reading '{filename}': {e}"

    lines, had_trailing_nl = _split_lines(raw)
    total = len(lines)

    # --- Dispatch ----------------------------------------------------------
    try:
        if mode == "find_replace":
            if search_text is None or replacement is None:
                return (
                    "Error: 'find_replace' mode requires "
                    "'search_text' and 'replacement'."
                )
            if not isinstance(search_text, str) or not isinstance(replacement, str):
                return "Error: 'search_text' and 'replacement' must be strings."
            if search_text == "":
                return "Error: 'search_text' must be non-empty."

            # Collect non-overlapping match positions
            positions = []
            pos = 0
            while True:
                idx = raw.find(search_text, pos)
                if idx == -1:
                    break
                positions.append(idx)
                pos = idx + len(search_text)
            count = len(positions)

            if count == 0:
                return (
                    "Error: No match found. Check whitespace/indentation."
                )

            if not replace_all:
                if count > 1:
                    line_nums = [raw.count("\n", 0, p) + 1 for p in positions]
                    return (
                        f"Error: Found {count} matches in '{filename}' at "
                        f"lines {line_nums}. Narrow your 'search_text' to a "
                        "unique snippet, or pass replace_all=True to replace "
                        "every match."
                    )
                # exactly one match
                match_line = raw.count("\n", 0, positions[0]) + 1
                new_raw = raw.replace(search_text, replacement, 1)
                summary = (
                    f"find_replace: replaced 1 occurrence at line "
                    f"{match_line} in '{filename}'."
                )
            else:
                new_raw = raw.replace(search_text, replacement)
                summary = (
                    f"find_replace: replaced {count} occurrence(s) in "
                    f"'{filename}'."
                )

        elif mode == "replace_range":
            if start_line is None or end_line is None or replacement is None:
                return (
                    "Error: 'replace_range' mode requires 'start_line', "
                    "'end_line', and 'replacement'."
                )
            if not isinstance(start_line, int) or not isinstance(end_line, int):
                return "Error: 'start_line' and 'end_line' must be integers."
            if start_line < 1:
                return (
                    f"Error: 'start_line' must be >= 1 (got {start_line}). "
                    "Lines are 1-indexed."
                )
            if end_line > total:
                return (
                    f"Error: 'end_line' ({end_line}) is beyond the last line "
                    f"of '{filename}' ({total})."
                )
            if start_line > end_line:
                return (
                    f"Error: 'start_line' ({start_line}) must be <= "
                    f"'end_line' ({end_line})."
                )

            before = lines[: start_line - 1]
            after = lines[end_line:]
            repl_lines = _split_content_lines(replacement)
            new_lines = before + repl_lines + after
            new_raw = _rejoin(new_lines, had_trailing_nl)
            summary = (
                f"replace_range: replaced lines {start_line}-{end_line} "
                f"({end_line - start_line + 1} line(s)) with "
                f"{len(repl_lines)} line(s) in '{filename}'."
            )

        elif mode == "insert":
            if line is None or content is None:
                return (
                    "Error: 'insert' mode requires 'line' and 'content'."
                )
            if not isinstance(line, int):
                return "Error: 'line' must be an integer."
            if line < 0:
                return (
                    f"Error: 'line' must be >= 0 (got {line}). "
                    "Use 0 to insert at the top of the file."
                )
            # Clamp 'line' past EOF to "append at end" — the caller clearly
            # wants the content added; rejecting just forces them to re-count.
            clamped = line if line <= total else total
            before = lines[:clamped]
            after = lines[clamped:]
            ins_lines = _split_content_lines(content)
            new_lines = before + ins_lines + after
            new_raw = _rejoin(new_lines, had_trailing_nl)
            summary = (
                f"insert: inserted {len(ins_lines)} line(s) after line {clamped} "
                f"in '{filename}' (now {len(new_lines)} line(s))."
                + (" [line clamped from {line} to {clamped}]" if clamped != line else "")
            ).format(line=line, clamped=clamped)

    except Exception as e:
        return f"Error: {e}"

    # --- Apply -------------------------------------------------------------
    if new_raw == raw:
        return f"No change to '{filename}' (text already matches the desired state)."

    try:
        _write_atomic(filepath, new_raw)
    except Exception as e:
        return f"Error writing '{filename}': {e}"

    diff = _git_diff(filepath, base_dir)
    return f"{summary}\n\n{diff}"


schema = {
    "type": "function",
    "function": {
        "name": "edit_file",
        "description": (
            "Surgical file editor. Three modes: find_replace, replace_range, insert. "
            "Use create_file for full-file rewrites. "
            "Each call picks ONE mode and passes that mode's keyword args. "
            "Use find_replace when the snippet is unique and line counts are awkward "
            "(exact-string match; replace_all=True to replace every occurrence). "
            "Use replace_range when the change spans a known inclusive line range "
            "[start_line, end_line]. "
            "Use insert to add new lines after a given line (0 = top of file, "
            "total = append at end; values past the end clamp to append). "
            "Returns a short summary plus the unified diff from `git diff`."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Path to the file (relative to cwd or absolute)."
                },
                "mode": {
                    "type": "string",
                    "enum": ["find_replace", "replace_range", "insert"],
                    "description": (
                        "Which edit mode to use. Pick exactly one. "
                        "'find_replace' (default snippet-edit, supports replace_all), "
                        "'replace_range' (replace an inclusive line range), "
                        "'insert' (add new lines after a given line)."
                    )
                },
                "search_text": {
                    "type": "string",
                    "description": (
                        "[find_replace] Exact substring to find. Must be non-empty. "
                        "If 2+ matches and replace_all=False, the call errors out "
                        "with the line numbers."
                    )
                },
                "replacement": {
                    "type": "string",
                    "description": (
                        "[find_replace, replace_range] Text to insert in place of the "
                        "match or the replaced line range. May contain newlines."
                    )
                },
                "replace_all": {
                    "type": "boolean",
                    "default": False,
                    "description": (
                        "[find_replace] If true, replace every occurrence of "
                        "search_text. If false (default), require exactly one match."
                    )
                },
                "start_line": {
                    "type": "integer",
                    "description": (
                        "[replace_range] First line of the inclusive range to "
                        "replace. 1-indexed."
                    )
                },
                "end_line": {
                    "type": "integer",
                    "description": (
                        "[replace_range] Last line of the inclusive range to "
                        "replace. 1-indexed."
                    )
                },
                "line": {
                    "type": "integer",
                    "description": (
                        "[insert] Insert content AFTER this line. 0 = top of file, "
                        "total_lines = append at end. Values past the end clamp "
                        "to append at end."
                    )
                },
                "content": {
                    "type": "string",
                    "description": (
                        "[insert] Text to insert. Include a trailing newline if "
                        "you want it on its own line."
                    )
                }
            },
            "required": ["filename", "mode"],
            "additionalProperties": False
        }
    }
}