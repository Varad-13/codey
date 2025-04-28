#!/usr/bin/env python3
import platform
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import ANSI
from .chat_runner import process_history
from .config import PROMPT_NAME, SHOW_SYSTEM_PROMPT
import importlib.resources as pkg_resources
import codey.prompts

# ANSI color codes
RESET      = "\033[0m"
USER_COLOR = "\033[92m"  # neon green for user input
TOOL_COLOR = "\033[95m"  # violet/purple for tool calls/results
CODEY_COLOR = "\033[32m"  # green for Codey responses

# Initialize prompt session and key bindings
session = PromptSession()
kb = KeyBindings()

@kb.add('c-n')  # Ctrl+N → insert newline

def _(event):
    """Ctrl+N → insert newline"""
    event.current_buffer.insert_text('\n')

@kb.add('enter')

def _(event):
    """Enter → submit buffer"""
    event.app.exit(result=event.current_buffer.text)


def load_prompt(name, os_info, shell_info):
    """
    Load prompt by filename from package resources (prompts subpackage),
    and inject OS/shell info.
    """
    try:
        with pkg_resources.open_text(codey.prompts, name) as f:
            prompt = f.read()
        # Inject dynamic information into prompt text
        prompt = prompt.replace("{os}", os_info)
        prompt = prompt.replace("{shell}", shell_info)
        return prompt
    except (FileNotFoundError, ModuleNotFoundError) as e:
        print(f"Error loading prompt '{name}': {e}")
        return ""


def main():
    # Detect OS and shell
    os_info = platform.system()
    shell_info = "/bin/sh"

    # Load the system prompt
    system_prompt = load_prompt(PROMPT_NAME, os_info, shell_info)

    # Initialize conversation history with system prompt
    history = [{"role": "system", "content": system_prompt}]

    # Main interaction loop
    while True:
        try:
            # Wrap prompt text in ANSI() so prompt_toolkit interprets the escapes
            prompt_message = ANSI(f"{USER_COLOR}👤 You (Ctrl+N newline, Enter to submit): {RESET}")
            text = session.prompt(
                prompt_message,
                multiline=True,
                key_bindings=kb
            )
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            sys.exit(0)

        # Handle exit commands
        if text.strip().lower() in ("exit", "quit"):
            print("Goodbye!")
            sys.exit(0)

        # Append user message and process
        history.append({"role": "user", "content": text})
        history, assistant_reply = process_history(history)

        # Display the assistant's response
        print(f"\n{CODEY_COLOR}🤖 Codey: {assistant_reply}{RESET}")
        print(f"{CODEY_COLOR}" + '-'*60 + f"{RESET}\n")


if __name__ == "__main__":
    main()
