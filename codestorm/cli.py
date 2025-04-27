#!/usr/bin/env python3
import platform
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from .chat_runner import process_history
from .config import PROMPT_NAME, SHOW_SYSTEM_PROMPT
import importlib.resources as pkg_resources
import codestorm.prompts

# Initialize prompt session and key bindings
session = PromptSession()
kb = KeyBindings()

@kb.add('c-n')  # Ctrl+J is ASCII newline

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
        with pkg_resources.open_text(codestorm.prompts, name) as f:
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
    if SHOW_SYSTEM_PROMPT:
        print(f"System prompt loaded.\n{'-'*60}")

    # Main interaction loop
    while True:
        try:
            text = session.prompt(
                "You (Ctrl+N newline, Enter to submit): ",
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
        print(f"\nAssistant: {assistant_reply}\n{'-'*60}")


if __name__ == "__main__":
    main()