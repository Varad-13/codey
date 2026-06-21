"""
Delegate a task to an autonomous subagent that has its own tool loop.

The subagent can browse the web, run shell commands, read/write files,
search code, and more — orchestrator just describes the goal.
"""

import json
import os

from codey.config import client, MODEL_NAME, SHOW_TOOL_CALLS
from codey.utils import assert_within_project

_SUBAGENT_COLOR = "\033[33m"   # yellow — distinct from main agent and tool output
_RESET          = "\033[0m"

_DEFAULT_TOOLS = [
    "web", "shell", "read_files", "grep",
    "create_file", "edit_file", "git", "calculate",
]

_SUBAGENT_SYSTEM = """\
You are a focused subagent completing a specific task assigned by an orchestrator.

Work autonomously using your tools. Do not ask clarifying questions — make your best
effort with what you have been given.

When your task is complete, return a clear, structured summary:
- For research: key findings, links, code examples
- For code changes: what you changed and why (include file names)
- For mixed tasks: both

Be thorough but stay on task. Avoid unnecessary side effects.\
"""

_MAX_ROUNDS = 25
_TRUNCATE   = 220


def _lazy_tools():
    """Lazy import to avoid circular dependency (delegate is part of the tools package)."""
    from codey.tools import TOOL_MAP, tools as all_schemas  # noqa: PLC0415
    return TOOL_MAP, all_schemas


def _call(name: str, args: dict):
    tool_map, _ = _lazy_tools()
    func = tool_map.get(name)
    if not func:
        return f"Error: unknown tool '{name}'"
    try:
        return func(**args)
    except Exception as e:
        return f"Error in {name}: {e}"


def _tool_content(result):
    """Return the value to use as the 'content' field in a tool-role message."""
    if isinstance(result, dict) and "__image__" in result:
        return [
            {"type": "text",      "text": result.get("text", "Image:")},
            {"type": "image_url", "image_url": {"url": result["__image__"]}},
        ]
    return json.dumps(result)


def _run(task: str, allowed: list[str]) -> str:
    """Inner agent loop for the subagent."""
    _, all_schemas = _lazy_tools()
    schemas = [s for s in all_schemas if s.get("function", {}).get("name") in allowed]

    history = [
        {"role": "system", "content": _SUBAGENT_SYSTEM},
        {"role": "user",   "content": task},
    ]

    for _ in range(_MAX_ROUNDS):
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=history,
            tools=schemas,
            tool_choice="auto",
        )
        msg        = resp.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None) or []

        if not tool_calls:
            return msg.content or ""

        # Append the assistant turn (may include reasoning text before tool calls)
        history.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id":   tc.id,
                    "type": "function",
                    "function": {
                        "name":      tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in tool_calls
            ],
        })

        for tc in tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except Exception:
                args = {}

            if SHOW_TOOL_CALLS:
                raw = json.dumps(args)
                display = raw[:_TRUNCATE] + "…" if len(raw) > _TRUNCATE else raw
                print(f"  {_SUBAGENT_COLOR}↳ {name}({display}){_RESET}")

            result  = _call(name, args)
            content = _tool_content(result)

            history.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "name":         name,
                "content":      content,
            })

    return f"[Subagent stopped after {_MAX_ROUNDS} rounds without finishing]"


# ── Public tool ──────────────────────────────────────────────────────────────

def delegate(
    task: str,
    tools: list = None,
    files: list = None,
    suggested_patch: str = "",
) -> str:
    """
    Spin up an autonomous subagent to complete a task end-to-end.
    Returns a summary of what was found or done.
    """
    allowed = tools if tools is not None else _DEFAULT_TOOLS

    # Build the full task prompt
    parts = [task]

    if files:
        base_dir = os.getcwd()
        snippets = []
        for fname in files:
            fpath = os.path.join(base_dir, fname)
            try:
                assert_within_project(fpath, base_dir)
                with open(fpath, "r", encoding="utf-8") as f:
                    snippets.append(f"### {fname}\n```\n{f.read()}\n```")
            except Exception as e:
                snippets.append(f"### {fname}\n[unreadable: {e}]")
        if snippets:
            parts.append("## Relevant files\n" + "\n\n".join(snippets))

    if suggested_patch:
        parts.append(
            f"## Suggested patch (intent — adapt to fit the real file)\n```\n{suggested_patch}\n```"
        )

    full_task = "\n\n".join(parts)

    print(f"  {_SUBAGENT_COLOR}[Subagent] tools: {', '.join(allowed)}{_RESET}")
    summary = _run(full_task, allowed)
    print(f"  {_SUBAGENT_COLOR}[Subagent done]{_RESET}")
    return summary


schema = {
    "type": "function",
    "function": {
        "name": "delegate",
        "description": (
            "Spin up an autonomous subagent to complete a task end-to-end. "
            "The subagent runs its own tool loop — it can browse the web, run shell commands, "
            "read/write files, search code, and more. "
            "Use for: research ('find oauth docs for Bruno'), multi-step setup tasks, "
            "focused code edits, or anything that needs several tool calls to complete. "
            "The subagent works autonomously and returns a structured summary."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": (
                        "Complete description of what the subagent should accomplish. "
                        "Include the goal, relevant constraints, and what a good result looks like. "
                        "Example: 'Find the official Bruno API client docs for setting up OAuth 2.0 "
                        "with PKCE. Return the key steps and any code examples.'"
                    )
                },
                "tools": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        f"Tool names available to the subagent. Defaults to {_DEFAULT_TOOLS}. "
                        "Use ['web'] to restrict to pure research, or omit to allow everything."
                    )
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Relative paths of local files to include as context (for code tasks)."
                },
                "suggested_patch": {
                    "type": "string",
                    "description": "Pseudocode or diff sketch hinting at the intended code change (for code tasks)."
                }
            },
            "required": ["task"],
            "additionalProperties": False
        }
    }
}
