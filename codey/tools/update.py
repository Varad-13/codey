# codey/tools/update.py
"""
LLM-callable `update` tool. The model must always go through the existing
`ask()` tool to get explicit user confirmation before this tool will
run `pip install`. We never let the model invoke pip directly without
consent.
"""

from .ask import ask
from ..update import CURRENT_VERSION, check_for_update, perform_update


def update() -> str:
    """Check for a newer Codey release; require user confirmation; install."""
    info = check_for_update(force=True)
    if not info:
        return "Codey is already up to date (v{0}).".format(CURRENT_VERSION)

    new_v = info.get("version", "?")
    question = (
        "Codey v{cur} -> v{new} is available. "
        "Upgrade now? (release notes will be shown)"
    ).format(cur=CURRENT_VERSION, new=new_v)

    answer = ask(question, options=["Yes, upgrade", "No, skip"])

    if answer not in ("Yes, upgrade", "yes"):
        return "Update skipped by user."

    ok, msg = perform_update(info)
    return msg


schema = {
    "type": "function",
    "function": {
        "name": "update",
        "description": (
            "Check for a newer version of Codey and, with explicit user "
            "confirmation, install it from GitHub Releases. Always prompts "
            "the user before running pip."
        ),
        "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
    },
}