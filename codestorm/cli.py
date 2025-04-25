# cli.py
#!/usr/bin/env python3
import sys
import os
from .chat_runner import process_history
from .config import PROMPT_NAME
import importlib.resources as pkg_resources
import codestorm.prompts


def load_prompt(name, shell_info):
    # Load prompt by filename from package resources (prompts subpackage)
    try:
        with pkg_resources.open_text(codestorm.prompts, name) as f:
            # Inject shell info into prompt text
            prompt = f.read()
            return prompt.replace("{shell}", shell_info)
    except (FileNotFoundError, ModuleNotFoundError) as e:
        print(f"Error loading prompt '{name}': {e}")
        return ""  # fallback empty prompt

def main():
    # Determine shell info to inject based on OS
    if sys.platform.startswith("win"):
        shell_info = "PowerShell"
    else:
        shell_info = "/bin/sh"

    system_prompt = load_prompt(PROMPT_NAME, shell_info)

    history = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    while True:
        try:
            user_input = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            sys.exit(0)

        if user_input.strip().lower() in ("exit", "quit"):
            print("Goodbye!")
            sys.exit(0)

        history.append({"role": "user", "content": user_input})
        history, assistant_reply = process_history(history)

        print(f"\nAssistant: {assistant_reply}\n" + "-"*60)


if __name__ == "__main__":
    main()
