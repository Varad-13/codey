import os


def assert_within_project(filepath: str, base_dir: str) -> None:
    """Raise ValueError if filepath resolves outside base_dir."""
    real_base = os.path.realpath(base_dir)
    real_path = os.path.realpath(filepath)
    if not (real_path == real_base or real_path.startswith(real_base + os.sep)):
        raise ValueError("Path is outside the project directory.")


def trim_history(history: list, max_messages: int = 100, tool_result_max: int = 3000) -> list:
    """
    Keep history size bounded and truncate oversized tool results in older turns.
    The system message is always preserved.
    """
    system_msgs = [m for m in history if m.get("role") == "system"]
    other_msgs  = [m for m in history if m.get("role") != "system"]

    if len(other_msgs) > max_messages:
        other_msgs = other_msgs[-max_messages:]

    # Truncate long tool results outside the most recent 20 messages
    keep_tail = 20
    cutoff = max(0, len(other_msgs) - keep_tail)
    for i in range(cutoff):
        msg = other_msgs[i]
        if msg.get("role") == "tool":
            content = msg.get("content", "")
            if isinstance(content, str) and len(content) > tool_result_max:
                other_msgs[i] = {**msg, "content": content[:tool_result_max] + "\n... [truncated]"}

    return system_msgs + other_msgs
