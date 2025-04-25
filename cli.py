# cli.py
#!/usr/bin/env python3
import sys
import platform
from chat_runer import process_history
import os
import config

def load_prompt(current_os):
    with open(config.PROMPT_PATH, 'r', encoding='utf-8') as f:
        raw_prompt = f.read()
    return raw_prompt.format(current_os=current_os)

def main():
    current_os = platform.system()

    system_prompt = load_prompt(current_os)

    # Initialize conversation with your system prompt
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
