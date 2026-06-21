import hashlib
import json
import os
from pathlib import Path

_HISTORY_DIR = Path.home() / ".codey" / "history"


def _history_path(project_dir: str) -> Path:
    real = os.path.realpath(project_dir)
    h = hashlib.md5(real.encode()).hexdigest()[:8]
    name = os.path.basename(real) or "root"
    _HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    return _HISTORY_DIR / f"{name}-{h}.jsonl"


def load_history(project_dir: str) -> list:
    """Return persisted non-system messages for this project directory."""
    path = _history_path(project_dir)
    if not path.exists():
        return []
    messages = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return messages


def save_messages(project_dir: str, messages: list) -> None:
    """Append messages to the project's history file."""
    path = _history_path(project_dir)
    with open(path, "a", encoding="utf-8") as f:
        for msg in messages:
            f.write(json.dumps(msg) + "\n")
