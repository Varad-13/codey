#!/usr/bin/env python3
import base64
import importlib.resources as pkg_resources
import mimetypes
import os
import platform
import re
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.key_binding import KeyBindings

from . import __version__
from .chat_runner import process_history
from .config import MODEL_NAME, PROMPT_NAME, ENABLED_TOOLS, PROVIDER
from .persistence import list_sessions, load_session, new_session_path, save_messages, load_session_meta, save_session_meta
from .tools import TOOL_MAP
from .update import check_for_update, format_update_notice, perform_update

import codey.prompts

RESET      = "\033[0m"
DIM        = "\033[2m"
USER_COLOR = "\033[92m"
TOOL_COLOR = "\033[95m"

# File extensions treated as images (sent as vision content blocks)
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

# Quoted Windows path:  "C:\path with spaces\file.png"  or  'C:\...'
_QUOTED_PATH_RE = re.compile(r'["\']([A-Za-z]:[/\\].+?|~/[^"\']+|/[^"\']+)["\']')
# Unquoted path (no spaces):  C:\foo\bar.png  ~/foo  /tmp/x
_UNQUOTED_PATH_RE = re.compile(
    r'(?:^|(?<=\s))([A-Za-z]:[/\\]\S+|~/?\S+|/\S+)(?=\s|$)',
    re.MULTILINE,
)


def _extract_paths(text: str) -> list:
    """Return candidate file path strings from the message, deduped, quoted first."""
    seen: set = set()
    paths: list = []
    for m in _QUOTED_PATH_RE.finditer(text):
        p = m.group(1)
        if p not in seen:
            seen.add(p)
            paths.append(p)
    for m in _UNQUOTED_PATH_RE.finditer(text):
        p = m.group(1).rstrip(".,;:\"'")
        if p not in seen:
            seen.add(p)
            paths.append(p)
    return paths


def _grab_clipboard_image() -> str | None:
    """Return base64-encoded PNG from the system clipboard, or None."""
    try:
        import io
        from PIL import ImageGrab
        img = ImageGrab.grabclipboard()
        if img is None:
            return None
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None


def _attach_path(path: str, attachments: list) -> None:
    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        return
    ext = os.path.splitext(path)[1].lower()
    if ext in _IMAGE_EXTS:
        try:
            with open(path, "rb") as f:
                data = f.read()
            mime = mimetypes.guess_type(path)[0] or "image/png"
            b64  = base64.b64encode(data).decode()
            attachments.append({
                "type":      "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
            })
            print(f"{TOOL_COLOR}Attached image: {path}{RESET}")
        except Exception as e:
            print(f"{TOOL_COLOR}Could not attach {path}: {e}{RESET}")
    else:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            attachments.append({
                "type": "text",
                "text": f"\n[File: {path}]\n```\n{content}\n```",
            })
            print(f"{TOOL_COLOR}Attached file: {path}{RESET}")
        except Exception as e:
            print(f"{TOOL_COLOR}Could not attach {path}: {e}{RESET}")


def _build_content(text: str):
    """
    Scan the message for file paths and the @image trigger.
      - image files  → image_url content block (vision models see them)
      - other files  → fenced text block
      - @image       → grab current clipboard image and attach it

    Returns a plain string if no attachments, or a content list otherwise.
    """
    attachments: list = []

    # Clipboard image trigger: user types @image anywhere in the message
    if "@image" in text:
        b64 = _grab_clipboard_image()
        if b64:
            attachments.append({
                "type":      "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            })
            print(f"{TOOL_COLOR}Attached clipboard image{RESET}")
        else:
            print(f"{TOOL_COLOR}@image: no image found in clipboard (install Pillow for clipboard support){RESET}")

    for raw in _extract_paths(text):
        _attach_path(raw, attachments)

    if not attachments:
        return text

    return [{"type": "text", "text": text}] + attachments


# ---------------------------------------------------------------------------
# Lazy prompt session / key bindings
#
# PromptSession() touches the Win32 console during construction, which means
# importing cli.py from a non-interactive environment (CI, `codey update`,
# `codey --version`) raises NoConsoleScreenBufferError. We construct them on
# first use instead.
# ---------------------------------------------------------------------------
_session = None
_kb = None


def _get_prompt_session():
    global _session
    if _session is None:
        _session = PromptSession()
    return _session


def _get_key_bindings():
    global _kb
    if _kb is None:
        _kb = KeyBindings()

        @_kb.add("c-n")
        def _(event):
            """Ctrl+N — insert newline"""
            event.current_buffer.insert_text("\n")

        @_kb.add("enter")
        def _(event):
            """Enter — submit"""
            event.app.exit(result=event.current_buffer.text)

    return _kb


def _fmt_date(ts: float) -> str:
    from datetime import datetime
    dt = datetime.fromtimestamp(ts)
    now = datetime.now()
    delta = (now.date() - dt.date()).days
    if delta == 0:
        return dt.strftime("Today      %H:%M")
    if delta == 1:
        return dt.strftime("Yesterday  %H:%M")
    if delta < 7:
        return dt.strftime("%A    %H:%M")
    return dt.strftime("%b %d, %Y      ")


def _pick_session(project_dir: str):
    """
    Display a session picker and return (session_path, prior_messages).
    Returns a fresh path with no messages if the user picks New or there are no sessions.
    """
    sessions = list_sessions(project_dir)
    if not sessions:
        return new_session_path(project_dir), []

    project_name = os.path.basename(os.path.realpath(project_dir))
    print(f"\n{TOOL_COLOR}Sessions — {project_name}{RESET}\n")

    for i, s in enumerate(sessions, 1):
        date_str = _fmt_date(s["mtime"])
        preview  = s["preview"]
        if len(preview) > 40:
            preview = preview[:40] + "…"
        count_str = f"({s['count']} msgs)"
        tok = s.get("tokens", {})
        if tok.get("total_tokens"):
            cost_part = f" ${tok['cost']:.4f}" if tok.get("cost") else ""
            tok_str = f"  {DIM}in:{tok['prompt_tokens']} out:{tok['completion_tokens']} tot:{tok['total_tokens']}{cost_part}{RESET}"
        else:
            tok_str = ""
        print(f"  {DIM}[{i}]{RESET} {date_str}  {DIM}{count_str:12}{RESET}  {preview}{tok_str}")

    print(f"\n  {DIM}[N]{RESET}  New session\n")

    while True:
        try:
            raw = input(f"{USER_COLOR}Select [{1}–{len(sessions)}/N]:{RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            sys.exit(0)

        if raw in ("n", ""):
            return new_session_path(project_dir), []
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(sessions):
                s = sessions[idx]
                prior = load_session(s["path"])
                print(f"{TOOL_COLOR}Resumed session ({s['count']} messages).{RESET}")
                return s["path"], prior
        print(f"  Enter a number 1–{len(sessions)} or N for a new session.")


def load_prompt(name: str, os_info: str, shell_info: str) -> str:
    try:
        with pkg_resources.open_text(codey.prompts, name) as f:
            prompt = f.read()
        return prompt.replace("{os}", os_info).replace("{shell}", shell_info)
    except (FileNotFoundError, ModuleNotFoundError) as e:
        print(f"Error loading prompt '{name}': {e}")
        return ""


def _dispatch_argv(argv):
    """Inspect argv for --version/-V and `update` subcommand before
    starting the chat loop. Returns True if a dispatch was handled.
    """
    args = list(argv)

    # --version / -V anywhere in argv
    for a in args:
        if a in ("--version", "-V"):
            print("codey {0}".format(__version__))
            sys.exit(0)

    # `update` subcommand: standalone token (allowing leading flags)
    for a in args:
        if a == "update":
            ok, msg = perform_update()
            print(msg, file=sys.stderr)
            sys.exit(0 if ok else 1)

    return False


def main():
    # Handle CLI subcommands / flags before doing anything else
    if _dispatch_argv(sys.argv[1:]):
        return

    os_info    = platform.system()
    shell_info = "/bin/sh"

    system_prompt = load_prompt(PROMPT_NAME, os_info, shell_info)

    # Append the live tool list so the model always knows exactly what's available
    active_tools = [name for name in TOOL_MAP if not ENABLED_TOOLS or name in ENABLED_TOOLS]
    system_prompt += (
        f"\n\n## Active tools in this session\n"
        f"{', '.join(active_tools)}\n\n"
        "**URL rule**: when the user's message contains a URL, call "
        "`web(action='navigate', url=<url>)` immediately — do not ask them to copy "
        "or summarise the content for you."
    )

    _update_info = check_for_update()
    if _update_info:
        print(format_update_notice(_update_info), file=sys.stderr)

    session_path, prior = _pick_session(os.getcwd())

    history = [{"role": "system", "content": system_prompt}]
    history.extend(prior)

    # Load any existing token counts for a resumed session
    session_tokens = load_session_meta(session_path)
    if not session_tokens:
        session_tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cost": 0.0}

    def _print_token_summary():
        t = session_tokens
        if t["total_tokens"]:
            cost_str = f"  cost: ${t['cost']:.6f}" if t.get("cost") else ""
            print(
                f"{TOOL_COLOR}Tokens — in: {t['prompt_tokens']}  "
                f"out: {t['completion_tokens']}  "
                f"total: {t['total_tokens']}{cost_str}{RESET}"
            )

    print(f"\n{TOOL_COLOR}Provider: {PROVIDER}  Model: {MODEL_NAME}  Tools: {', '.join(active_tools)} — type 'exit' to quit{RESET}")
    print(f"{TOOL_COLOR}Tip: paste a file path to attach it | type @image to attach clipboard image{RESET}\n")

    # Lazy-init now that we know we have a real console.
    session = _get_prompt_session()
    kb = _get_key_bindings()

    while True:
        try:
            text = session.prompt(
                ANSI(f"{USER_COLOR}You{RESET} (Ctrl+N newline): "),
                multiline=True,
                key_bindings=kb,
            )
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            _print_token_summary()
            sys.exit(0)

        if text.strip().lower() in ("exit", "quit"):
            print("Goodbye!")
            _print_token_summary()
            sys.exit(0)

        content = _build_content(text)

        start_idx = len(history)
        history.append({"role": "user", "content": content})

        try:
            history, _, usage = process_history(history, MODEL_NAME)
        except KeyboardInterrupt:
            print(f"\n{TOOL_COLOR}[Interrupted — returning to prompt]{RESET}")
            # Roll back the user message so the incomplete turn isn't saved
            history = history[:start_idx]
            print(f"{TOOL_COLOR}" + "-" * 60 + f"{RESET}\n")
            continue

        # Accumulate token usage for this session
        if usage:
            for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
                session_tokens[k] = session_tokens.get(k, 0) + usage.get(k, 0)
            session_tokens["cost"] = session_tokens.get("cost", 0.0) + usage.get("cost", 0.0)
            save_session_meta(session_path, session_tokens)

        save_messages(session_path, history[start_idx:])

        print(f"{TOOL_COLOR}" + "-" * 60 + f"{RESET}\n")


if __name__ == "__main__":
    main()
