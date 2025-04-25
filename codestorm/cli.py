# cli.py
#!/usr/bin/env python3
import sys
from .chat_runner import process_history

def main():
    # Initialize conversation with your system prompt
    history = [
        {
            "role": "system",
            "content": (
                """
                Give preference to using given tools. All responses must be relevant to current codebase only.
                You are an autonomous coding assistant and must require minimal user prompting. When you act, follow these rules:
                1. Self-inspect first: call tools to discover context.
                2. Summarize actions briefly (200–300 words).
                3. Only commit via git after edits.
                4. Do not re-ask for obvious details.
                """
            )
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
