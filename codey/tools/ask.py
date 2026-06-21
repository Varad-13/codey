import sys

ASK_COLOR = "\033[96m"   # cyan — visually distinct from tool/codey output
RESET     = "\033[0m"
DIM       = "\033[2m"


def ask(question: str, options: list = None) -> str:
    """
    Present a question to the user and return their response.
    If options are provided the user may select one by number or type a custom answer.
    """
    print(f"\n{ASK_COLOR}? {question}{RESET}")

    if options:
        for i, opt in enumerate(options, 1):
            print(f"  {DIM}[{i}]{RESET} {opt}")
        print()
        sys.stdout.write(f"{ASK_COLOR}Enter number or type a reply:{RESET} ")
    else:
        sys.stdout.write(f"{ASK_COLOR}Your reply:{RESET} ")

    sys.stdout.flush()

    try:
        answer = sys.stdin.readline().strip()
    except (EOFError, KeyboardInterrupt):
        return "(no response)"

    # If the user typed a valid option number, resolve it to the option text
    if options and answer.isdigit():
        idx = int(answer) - 1
        if 0 <= idx < len(options):
            return options[idx]

    return answer if answer else "(no response)"


schema = {
    "type": "function",
    "function": {
        "name": "ask",
        "description": (
            "Ask the user a question and wait for their response before continuing. "
            "Use this whenever you need a decision, preference, or clarification. "
            "Supply 'options' to offer numbered choices; the user can pick one or type a custom answer."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to present to the user."
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional suggested answers the user can select by number."
                }
            },
            "required": ["question"],
            "additionalProperties": False
        }
    }
}
