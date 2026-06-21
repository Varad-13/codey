import os


def assert_within_project(filepath: str, base_dir: str) -> None:
    """Raise ValueError if filepath resolves outside base_dir."""
    real_base = os.path.realpath(base_dir)
    real_path = os.path.realpath(filepath)
    if not (real_path == real_base or real_path.startswith(real_base + os.sep)):
        raise ValueError("Path is outside the project directory.")


def sanitize_tool_sequences(msgs: list) -> list:
    """
    Remove messages that would cause a 400 from the API:
      - tool messages whose tool_call_id has no matching assistant tool_calls entry
      - assistant+tool_calls messages with zero matching tool results

    Runs two passes so that removing one kind of orphan doesn't leave new ones.
    """
    for _ in range(2):
        # IDs declared in assistant tool_calls
        declared = {
            tc["id"]
            for m in msgs
            for tc in (m.get("tool_calls") or [])
            if tc.get("id")
        }
        # Drop tool messages with no declared parent
        msgs = [
            m for m in msgs
            if not (m.get("role") == "tool" and m.get("tool_call_id") not in declared)
        ]
        # IDs that actually have a result
        with_results = {
            m["tool_call_id"]
            for m in msgs
            if m.get("role") == "tool" and m.get("tool_call_id")
        }
        # Drop assistant+tool_calls where NO results are present
        msgs = [
            m for m in msgs
            if not (
                m.get("role") == "assistant"
                and m.get("tool_calls")
                and not {tc["id"] for tc in m["tool_calls"] if tc.get("id")} & with_results
            )
        ]
    return msgs


def trim_history(history: list, max_messages: int = 100, tool_result_max: int = 3000) -> list:
    """
    Keep history size bounded and truncate oversized tool results in older turns.
    The system message is always preserved.

    The cut point is advanced past any leading tool messages so we never split
    an assistant+tool_calls / tool-result pair. A sanitization pass then removes
    any remaining orphans (e.g. from loaded sessions saved mid-crash).
    """
    system_msgs = [m for m in history if m.get("role") == "system"]
    other_msgs  = [m for m in history if m.get("role") != "system"]

    if len(other_msgs) > max_messages:
        cut = len(other_msgs) - max_messages
        # Advance past any tool messages so we never orphan a result
        while cut < len(other_msgs) and other_msgs[cut].get("role") == "tool":
            cut += 1
        other_msgs = other_msgs[cut:]

    # Belt-and-suspenders: clean up any orphans (covers loaded sessions too)
    other_msgs = sanitize_tool_sequences(other_msgs)

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
