import os
import subprocess
import sys
import threading
import time

# Active sessions keyed by session_id
_sessions: dict = {}


class _Session:
    def __init__(self, proc: subprocess.Popen):
        self.proc = proc
        self._buf: list = []
        self._lock = threading.Lock()
        t = threading.Thread(target=self._reader, daemon=True)
        t.start()

    def _reader(self):
        try:
            while True:
                chunk = self.proc.stdout.read(256)
                if not chunk:
                    break
                with self._lock:
                    self._buf.append(chunk.decode("utf-8", errors="replace"))
        except Exception:
            pass

    def drain(self, settle: float = 0.3, timeout: float = 10.0) -> str:
        """
        Collect buffered output.  Waits until no new bytes arrive for `settle`
        seconds, or until `timeout` seconds total have elapsed.
        """
        deadline = time.monotonic() + timeout
        last_activity = time.monotonic()
        prev_len = 0

        while time.monotonic() < deadline:
            time.sleep(0.05)
            with self._lock:
                cur_len = sum(len(s) for s in self._buf)
            if cur_len > prev_len:
                last_activity = time.monotonic()
                prev_len = cur_len
            elif time.monotonic() - last_activity >= settle:
                break

        with self._lock:
            out = "".join(self._buf)
            self._buf.clear()
        return out

    def send(self, text: str) -> None:
        line = text if text.endswith("\n") else text + "\n"
        self.proc.stdin.write(line.encode("utf-8"))
        self.proc.stdin.flush()

    def alive(self) -> bool:
        return self.proc.poll() is None

    def stop(self) -> None:
        try:
            self.proc.terminate()
        except Exception:
            pass


def terminal(
    action: str,
    command: str = "",
    text: str = "",
    session_id: str = "default",
    settle: float = 0.3,
    timeout: float = 10.0,
) -> str:
    """
    Manage a persistent interactive terminal session.

    action=start  — launch `command`, return its initial output
    action=send   — write `text` to stdin, return new output
    action=peek   — read any pending output without sending input
    action=stop   — terminate the session
    """
    if action == "start":
        if session_id in _sessions:
            if _sessions[session_id].alive():
                return (
                    f"Session '{session_id}' is already running. "
                    "Use action=stop first or choose a different session_id."
                )
            del _sessions[session_id]

        if not command:
            return "Error: 'command' is required for action=start."

        shell_cmd = (
            ["powershell", "-Command", command]
            if sys.platform.startswith("win")
            else ["/bin/sh", "-c", command]
        )

        proc = subprocess.Popen(
            shell_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            cwd=os.getcwd(),
        )
        session = _Session(proc)
        _sessions[session_id] = session

        output = session.drain(settle=settle, timeout=timeout)
        status = "running" if session.alive() else "exited immediately"
        header = f"[Session '{session_id}' started — {status}]"
        return f"{header}\n{output}" if output else header

    elif action == "send":
        session = _sessions.get(session_id)
        if not session:
            return f"No session '{session_id}'. Use action=start first."
        if not session.alive():
            code = session.proc.returncode
            del _sessions[session_id]
            return f"Session '{session_id}' already exited (code {code})."

        session.send(text)
        output = session.drain(settle=settle, timeout=timeout)

        if not session.alive():
            code = session.proc.returncode
            del _sessions[session_id]
            return f"{output}\n[Process exited with code {code}]"
        return output if output else "(no output)"

    elif action == "peek":
        session = _sessions.get(session_id)
        if not session:
            return f"No session '{session_id}'."
        output = session.drain(settle=settle, timeout=min(timeout, 2.0))
        if not session.alive():
            del _sessions[session_id]
            return f"{output}\n[Process has exited]"
        return output if output else "(no output)"

    elif action == "stop":
        session = _sessions.pop(session_id, None)
        if not session:
            return f"No session '{session_id}'."
        session.stop()
        return f"Session '{session_id}' terminated."

    else:
        return f"Unknown action '{action}'. Valid actions: start, send, peek, stop."


schema = {
    "type": "function",
    "function": {
        "name": "terminal",
        "description": (
            "Run an interactive terminal session for commands that prompt for input "
            "(Y/N confirmations, setup wizards, multi-step CLI tools). "
            "Workflow: start → read output → send responses one at a time → process exits or stop. "
            "Use 'peek' to check for output without sending input. "
            "Multiple concurrent sessions are supported via session_id."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["start", "send", "peek", "stop"],
                    "description": "start: launch command. send: write text to stdin. peek: read pending output. stop: terminate."
                },
                "command": {
                    "type": "string",
                    "description": "Shell command to run. Required for action=start."
                },
                "text": {
                    "type": "string",
                    "description": "Text to send to stdin (a newline is appended automatically). Used with action=send."
                },
                "session_id": {
                    "type": "string",
                    "description": "Name for this session. Defaults to 'default'. Use different IDs to run multiple sessions."
                },
                "settle": {
                    "type": "number",
                    "description": "Seconds of silence that signals output is complete. Default 0.3. Increase for slow commands."
                },
                "timeout": {
                    "type": "number",
                    "description": "Maximum seconds to wait for output. Default 10.0."
                }
            },
            "required": ["action"],
            "additionalProperties": False
        }
    }
}
