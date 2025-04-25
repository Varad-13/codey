# cli.py
#!/usr/bin/env python3
import sys
from .chat_runner import process_history
from .config import PROMPT_NAME
import importlib.resources as pkg_resources
from . import prompts

def load_prompt(name):
    # Load prompt by filename from package resources (prompts subpackage)
    try:
        with pkg_resources.open_text(prompts, name) as f:
            return f.read()
    except (FileNotFoundError, ModuleNotFoundError) as e:
        print(f"Error loading prompt '{name}': {e}")
        return ""  # fallback empty prompt

def main():
    system_prompt = load_prompt(PROMPT_NAME)

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
