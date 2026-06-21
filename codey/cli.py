#!/usr/bin/env python3
import importlib.resources as pkg_resources
import os
import platform
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.key_binding import KeyBindings

from .chat_runner import process_history
from .config import MODEL_NAME, PROMPT_NAME
from .persistence import load_history, save_messages

import codey.prompts

RESET       = "\033[0m"
USER_COLOR  = "\033[92m"
TOOL_COLOR  = "\033[95m"

session = PromptSession()
kb = KeyBindings()


@kb.add('c-n')
def _(event):
    """Ctrl+N — insert newline"""
    event.current_buffer.insert_text('\n')


@kb.add('enter')
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
    history = [{"role": "system", "content": system_prompt}]

    # Restore previous session for this project directory
    prior = load_history(os.getcwd())
    if prior:
        history.extend(prior)
        print(f"{TOOL_COLOR}Resumed session ({len(prior)} messages).{RESET}")

    print(f"{TOOL_COLOR}Model: {MODEL_NAME} — type 'exit' to quit{RESET}\n")

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

        start_idx = len(history)
        history.append({"role": "user", "content": text})

        # process_history streams the response directly to stdout
        history, _ = process_history(history, MODEL_NAME)

        # Persist everything added this turn
        save_messages(os.getcwd(), history[start_idx:])

        print(f"{TOOL_COLOR}" + '-' * 60 + f"{RESET}\n")


if __name__ == "__main__":
    main()
