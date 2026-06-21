import json
import logging
import os
import sys

from .config import (
    client, MODEL_NAME, SHOW_TOOL_CALLS, SHOW_TOOL_RESULTS,
    ENABLED_TOOLS, CONFIRM_SHELL, MAX_TOOL_ROUNDS,
)
from .tools import tools as tool_schemas, TOOL_MAP
from .utils import trim_history

RESET       = "\033[0m"
TOOL_COLOR  = "\033[95m"
CODEY_COLOR = "\033[32m"

ENABLE_LOGGING = False
logger = logging.getLogger('codey')
if not logger.handlers:
    if ENABLE_LOGGING:
        fh = logging.FileHandler(os.path.join(os.getcwd(), 'codey.log'))
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.setLevel(logging.DEBUG)
        logger.addHandler(fh)
    else:
        logger.addHandler(logging.NullHandler())
    logger.propagate = False

TRUNCATE_LIMIT = 250


def truncate_args(args):
    try:
        s = json.dumps(args)
        return s[:TRUNCATE_LIMIT] + '...' if len(s) > TRUNCATE_LIMIT else s
    except Exception:
        return str(args)


def call_tool(name, args):
    """Safely call a tool, with optional shell-command confirmation."""
    if name == "shell" and CONFIRM_SHELL:
        cmd = args.get("command", "")
        sys.stdout.write(f"{TOOL_COLOR}Shell: {cmd}{RESET}\nExecute? [y/N] ")
        sys.stdout.flush()
        answer = sys.stdin.readline().strip().lower()
        if answer != "y":
            return "Command execution cancelled by user."

    if SHOW_TOOL_CALLS:
        print(f"{TOOL_COLOR}Tool call: {name}({truncate_args(args)}){RESET}")
    logger.debug(f"TOOL_CALL name={name}")

    try:
        func = TOOL_MAP.get(name)
        if not func:
            msg = f"Error: Unknown tool '{name}'"
            logger.error(msg)
            print(f"{TOOL_COLOR}{msg}{RESET}")
            return msg
        result = func(**args)
        logger.debug(f"TOOL_RESULT name={name}")
        if SHOW_TOOL_RESULTS:
            if isinstance(result, dict) and "__image__" in result:
                print(f"{TOOL_COLOR}Tool result: [image] {result.get('text', '')}{RESET}")
            else:
                print(f"{TOOL_COLOR}Tool result: {result}{RESET}")
        return result
    except Exception as e:
        err = f"Error executing tool '{name}': {e}"
        logger.error(err)
        print(f"{TOOL_COLOR}{err}{RESET}")
        return err


def _active_tools():
    return [
        t for t in tool_schemas
        if not ENABLED_TOOLS or t.get("function", {}).get("name") in ENABLED_TOOLS
    ]


def process_history(history, model=MODEL_NAME):
    """
    Stream conversation history to the model, execute any tool calls,
    and return the updated history plus the assistant's final text response.
    """
    history = trim_history(history)

    for _ in range(MAX_TOOL_ROUNDS):
        stream = client.chat.completions.create(
            model=model,
            messages=history,
            tools=_active_tools(),
            tool_choice="auto",
            stream=True,
        )

        content_parts = []
        tool_calls_map = {}   # index -> {id, name, arguments}
        printed_prefix = False

        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            if delta.content:
                if not printed_prefix:
                    print(f"\n{CODEY_COLOR}Codey: ", end="", flush=True)
                    printed_prefix = True
                print(delta.content, end="", flush=True)
                content_parts.append(delta.content)

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_map:
                        tool_calls_map[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc.id:
                        tool_calls_map[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls_map[idx]["name"] += tc.function.name
                        if tc.function.arguments:
                            tool_calls_map[idx]["arguments"] += tc.function.arguments

        if printed_prefix:
            print(RESET, flush=True)

        content = "".join(content_parts)

        if tool_calls_map:
            tool_calls_list = [
                {
                    "id": v["id"],
                    "type": "function",
                    "function": {"name": v["name"], "arguments": v["arguments"]},
                }
                for _, v in sorted(tool_calls_map.items())
            ]

            history.append({
                "role": "assistant",
                "content": content or None,
                "tool_calls": tool_calls_list,
            })

            for tc in tool_calls_list:
                name = tc["function"]["name"]
                try:
                    args = json.loads(tc["function"]["arguments"])
                except Exception:
                    args = {}

                if ENABLED_TOOLS and name not in ENABLED_TOOLS:
                    result = f"Error: tool '{name}' is not enabled in this session."
                else:
                    result = call_tool(name, args)

                # Image results (e.g. screenshots) are sent as multimodal content
                # arrays so vision-capable models can see them directly.
                if isinstance(result, dict) and "__image__" in result:
                    tool_content = [
                        {"type": "text",      "text": result.get("text", "Image:")},
                        {"type": "image_url", "image_url": {"url": result["__image__"]}},
                    ]
                else:
                    tool_content = json.dumps(result)

                history.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": name,
                    "content": tool_content,
                })
            continue

        # No tool calls — this is the final response
        history.append({"role": "assistant", "content": content})
        return history, content

    msg = f"[Stopped after {MAX_TOOL_ROUNDS} tool-call rounds]"
    print(f"{TOOL_COLOR}{msg}{RESET}")
    history.append({"role": "assistant", "content": msg})
    return history, msg
