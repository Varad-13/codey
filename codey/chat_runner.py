import json
import os
import logging
from .config import client, MODEL_NAME, SHOW_TOOL_CALLS, SHOW_TOOL_RESULTS, ENABLED_TOOLS
from .tools import tools as tool_schemas, TOOL_MAP

# ANSI color codes
RESET       = "\033[0m"
TOOL_COLOR  = "\033[95m"  # violet/purple for tool calls/results
CODEY_COLOR = "\033[32m"  # green for Codey responses (unused here)

# Setup logging to file
log_file = os.path.join(os.getcwd(), 'codey.log')
logger = logging.getLogger('codey')
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.propagate = False

TRUNCATE_LIMIT = 100

def truncate_args(args):
    try:
        args_str = json.dumps(args)
        if len(args_str) > TRUNCATE_LIMIT:
            return args_str[:TRUNCATE_LIMIT] + '...'
        return args_str
    except Exception:
        return str(args)  # fallback


def call_tool(name, args):
    """
    Safely call the specified tool with arguments, catching exceptions.
    """
    if SHOW_TOOL_CALLS:
        truncated = truncate_args(args)
        print(f"{TOOL_COLOR}Tool call: {name}({truncated}){RESET}")
    logger.debug(f"TOOL_CALL name={name}")
    try:
        func = TOOL_MAP.get(name)
        if not func:
            msg = f"Error: Unknown tool '{name}'"
            logger.error(msg)
            print(f"{TOOL_COLOR}{msg}{RESET}")
            return msg
        result = func(**args)
        logger.debug(f"TOOL_RESULT name={name} result={result}")
        if SHOW_TOOL_RESULTS:
            print(f"{TOOL_COLOR}Tool result: {result}{RESET}")
        return result
    except Exception as e:
        err = f"Error executing tool '{name}': {e}"
        logger.error(err)
        print(f"{TOOL_COLOR}{err}{RESET}")
        return err


def process_history(history):
    """
    Sends the conversation `history` to the model, executes any tool calls,
    and returns the updated history plus the assistant's text response.
    """

    while True:
        #logger.debug(f"LLM_REQUEST history={history}")
        #logger.debug(f"LLM_REQUEST model={MODEL_NAME}")
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=history,
            tools = [
                t for t in tool_schemas
                if not ENABLED_TOOLS or t.get("function", {}).get("name") in ENABLED_TOOLS
            ],
            tool_choice="auto"
        )
        #logger.debug(f"LLM_RAW_RESPONSE {resp}")

        assistant_msg = resp.choices[0].message
        tool_calls = getattr(assistant_msg, "tool_calls", None)

        if tool_calls:
            # Append assistant's tool call request
            history.append({
                "role": "assistant",
                "tool_calls": [call.to_dict() for call in tool_calls],
                "content": None
            })

            for call in tool_calls:
                try:
                    args = json.loads(call.function.arguments)
                except Exception:
                    args = {}

                if ENABLED_TOOLS and call.function.name not in ENABLED_TOOLS:
                    continue

                result = call_tool(call.function.name, args)

                # Append tool result
                history.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": call.function.name,
                    "content": json.dumps(result)
                })
            continue  # loop again with updated history

        # Assistant gave final text
        assistant_text = assistant_msg.content or ""
        #logger.debug(f"LLM_OUTPUT_TEXT {assistant_text}")
        history.append({"role": "assistant", "content": assistant_text})
        return history, assistant_text
