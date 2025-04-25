# cli.py
#!/usr/bin/env python3
import sys
import platform
from .chat_runner import process_history
from .config import PROMPT_NAME, SHOW_SYSTEM_PROMPT
import importlib.resources as pkg_resources
import codestorm.prompts


def load_prompt(name, os_info, shell_info):
    # Load prompt by filename from package resources (prompts subpackage)
    try:
        with pkg_resources.open_text(codestorm.prompts, name) as f:
            prompt = f.read()
            # Inject os and shell info into prompt text
            prompt = prompt.replace("{os}", os_info)
            prompt = prompt.replace("{shell}", shell_info)
            return prompt
    except (FileNotFoundError, ModuleNotFoundError) as e:
        print(f"Error loading prompt '{name}': {e}")
        return ""  # fallback empty prompt

def main():
    # Determine OS and shell info
    os_info = platform.system()
    shell_info = "/bin/sh"  # fixed shell

    system_prompt = load_prompt(PROMPT_NAME, os_info, shell_info)

    history = []
    if SHOW_SYSTEM_PROMPT:
        history.append({"role": "system", "content": system_prompt})

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
