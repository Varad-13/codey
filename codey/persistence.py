import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

_HISTORY_DIR = Path.home() / ".codey" / "history"


# ── Internal helpers ─────────────────────────────────────────────────────────

def _project_key(project_dir: str) -> str:
    real = os.path.realpath(project_dir)
    h = hashlib.md5(real.encode()).hexdigest()[:8]
    name = os.path.basename(real) or "root"
    return f"{name}-{h}"


def _sessions_dir(project_dir: str) -> Path:
    d = _HISTORY_DIR / _project_key(project_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _read_jsonl(path: Path) -> list:
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


def _session_preview(messages: list) -> str:
    """Return a short preview string from the first user message."""
    for m in messages:
        if m.get("role") != "user":
            continue
        content = m.get("content", "")
        if isinstance(content, str):
            return content.replace("\n", " ")[:70]
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    return block["text"].replace("\n", " ")[:70]
    return ""


# ── Migration from old single-file format ───────────────────────────────────

def _migrate_old_format(project_dir: str) -> None:
    key = _project_key(project_dir)
    old_path = _HISTORY_DIR / f"{key}.jsonl"
    if not old_path.exists():
        return
    sessions_dir = _sessions_dir(project_dir)
    mtime = datetime.fromtimestamp(old_path.stat().st_mtime)
    new_path = sessions_dir / (mtime.strftime("%Y%m%d-%H%M%S") + ".jsonl")
    if not new_path.exists():
        old_path.rename(new_path)
    else:
        old_path.unlink()


# ── Public API ───────────────────────────────────────────────────────────────

def _meta_path(session_path: Path) -> Path:
    return session_path.with_suffix(".meta.json")


def load_session_meta(session_path: Path) -> dict:
    p = _meta_path(session_path)
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_session_meta(session_path: Path, meta: dict) -> None:
    p = _meta_path(session_path)
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(meta, f)
    except Exception:
        pass


def list_sessions(project_dir: str) -> list:
    """
    Return sessions for this project sorted newest-first.
    Each item: {path, mtime, count, preview, tokens}
    """
    _migrate_old_format(project_dir)
    d = _sessions_dir(project_dir)
    sessions = []
    for p in sorted(d.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True):
        msgs = _read_jsonl(p)
        if not msgs:
            continue
        sessions.append({
            "path":    p,
            "mtime":   p.stat().st_mtime,
            "count":   len(msgs),
            "preview": _session_preview(msgs),
            "tokens":  load_session_meta(p),
        })
    return sessions


def new_session_path(project_dir: str) -> Path:
    """Return a Path for a brand-new session (file is not created yet)."""
    d = _sessions_dir(project_dir)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return d / f"{ts}.jsonl"


def load_session(path: Path) -> list:
    """Load messages from a session file, excluding any system messages."""
    return [m for m in _read_jsonl(path) if m.get("role") != "system"]


def save_messages(session_path: Path, messages: list) -> None:
    """Append messages to the given session file."""
    with open(session_path, "a", encoding="utf-8") as f:
        for msg in messages:
            f.write(json.dumps(msg) + "\n")
