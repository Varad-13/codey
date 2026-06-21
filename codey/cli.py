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

from .chat_runner import process_history
from .config import MODEL_NAME, PROMPT_NAME, ENABLED_TOOLS
from .persistence import load_history, save_messages
from .tools import TOOL_MAP

import codey.prompts

RESET      = "\033[0m"
USER_COLOR = "\033[92m"
TOOL_COLOR = "\033[95m"

session = PromptSession()
kb = KeyBindings()

# File extensions treated as images (sent as vision content blocks)
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

# Quoted Windows path:  "C:\path with spaces\file.png"  or  'C:\...'
_QUOTED_PATH_RE = re.compile(r'["\']([A-Za-z]:[/\\].+?|~/[^\'"]+|/[^\'"]+)["\']')
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


@kb.add("c-n")
def _(event):
    """Ctrl+N — insert newline"""
    event.current_buffer.insert_text("\n")


@kb.add("enter")
def _(event):
    """Enter — submit"""
    event.app.exit(result=event.current_buffer.text)


def load_prompt(name: str, os_info: str, shell_info: str) -> str:
    try:
        with pkg_resources.open_text(codey.prompts, name) as f:
            prompt = f.read()
        return prompt.replace("{os}", os_info).replace("{shell}", shell_info)
    except (FileNotFoundError, ModuleNotFoundError) as e:
        print(f"Error loading prompt '{name}': {e}")
        return ""


def main():
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

    history = [{"role": "system", "content": system_prompt}]

    prior = load_history(os.getcwd())
    if prior:
        history.extend(prior)
        print(f"{TOOL_COLOR}Resumed session ({len(prior)} messages).{RESET}")

    print(f"{TOOL_COLOR}Model: {MODEL_NAME}  Tools: {', '.join(active_tools)} — type 'exit' to quit{RESET}")
    print(f"{TOOL_COLOR}Tip: paste a file path to attach it | type @image to attach clipboard image{RESET}\n")

    while True:
        try:
            text = session.prompt(
                ANSI(f"{USER_COLOR}You{RESET} (Ctrl+N newline): "),
                multiline=True,
                key_bindings=kb,
            )
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            sys.exit(0)

        if text.strip().lower() in ("exit", "quit"):
            print("Goodbye!")
            sys.exit(0)

        content = _build_content(text)

        start_idx = len(history)
        history.append({"role": "user", "content": content})

        history, _ = process_history(history, MODEL_NAME)

        save_messages(os.getcwd(), history[start_idx:])

        print(f"{TOOL_COLOR}" + "-" * 60 + f"{RESET}\n")


if __name__ == "__main__":
    main()
