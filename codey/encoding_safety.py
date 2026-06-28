"""
Encoding safety helpers for the Codey tool layer.

The problem
-----------
On Windows the active console code page is often 437 (OEM-US) or 1252
(Windows Latin-1), while Python 3.14's stdio defaults to that *console*
encoding, not UTF-8. When a child process (often PowerShell) emits a UTF-8
byte that has no mapping in that codepage -- classically the C1 range
0x80..0x9F (which includes 0x8F), plus anything outside Latin script --
subprocess's text-mode decode raises UnicodeDecodeError. The shell tool
surfaces that exception as the tool result, the model sees the traceback,
retries the call, and you get an infinite loop of context bloat.

The fix
-------
This module does NOT mutate global state, environment variables, or stdio
configuration. It only provides two pure helpers:

* ``safe_decode(data, *, encoding="utf-8", fallback="latin-1")`` --
  tolerant decode that never raises. Tries UTF-8 first with
  ``errors="replace"``; if the result still contains replacement chars,
  falls back to ``latin-1`` (which can decode any byte sequence). Always
  returns ``str``.

* ``run_capture(cmd, **kwargs)`` --
  thin wrapper around ``subprocess.run`` that captures stdout/stderr as
  bytes, then runs them through ``safe_decode``. Same return shape as
  ``subprocess.run``.

The tool layer (``codey/tools/shell.py``, ``codey/tools/terminal.py``)
imports these helpers explicitly. Nothing else in the codebase or in the
Python environment is touched.
"""

from __future__ import annotations

import subprocess
from typing import Mapping, Sequence


def safe_decode(
    data,
    *,
    preferred: str = "utf-8",
    fallback: str = "latin-1",
) -> str:
    """Decode bytes (or pass through str) without ever raising.

    Tries ``preferred`` first with ``errors="replace"``. If the result
    still contains U+FFFD chars (a strong signal the bytes are not in the
    preferred encoding), retries with ``fallback`` -- ``latin-1`` can
    decode any byte sequence so the fallback never raises either.
    """
    if isinstance(data, str):
        return data
    if data is None or len(data) == 0:
        return ""
    try:
        decoded = data.decode(preferred, errors="replace")
    except LookupError:
        # Unknown encoding name -- fall back to utf-8, which Python always
        # supports.
        decoded = data.decode("utf-8", errors="replace")
    if "\ufffd" in decoded and fallback and fallback != preferred:
        try:
            alt = data.decode(fallback, errors="replace")
        except LookupError:
            return decoded
        if alt.count("\ufffd") < decoded.count("\ufffd"):
            return alt
    return decoded


def run_capture(
    cmd: Sequence[str],
    *,
    timeout: float | None = None,
    cwd: str | None = None,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """``subprocess.run`` that captures raw bytes and decodes safely.

    Returns a ``CompletedProcess`` with ``.stdout`` and ``.stderr`` as
    ``str`` (possibly empty). Never raises from decoding; only OSError
    and TimeoutExpired propagate, as with the stdlib.
    """
    proc = subprocess.run(
        list(cmd),
        capture_output=True,
        timeout=timeout,
        cwd=cwd,
        env=env,
        check=False,
    )
    proc.stdout = safe_decode(proc.stdout)
    proc.stderr = safe_decode(proc.stderr)
    return proc