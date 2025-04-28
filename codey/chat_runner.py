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

def call_tool(name, args):
    """
    Safely call the specified tool with arguments, catching exceptions.
    """
    if SHOW_TOOL_CALLS:
        print(f"{TOOL_COLOR}🔧 Tool call: {name}({args}){RESET}")
    logger.debug(f"TOOL_CALL name={name}")
    try:
        func = TOOL_MAP.get(name)
        if not func:
            msg = f"Error: Unknown tool '{name}'"
            logger.error(msg)
            print(f"{TOOL_COLOR}⚠️  {msg}{RESET}")
            return msg
        result = func(**args)
        logger.debug(f"TOOL_RESULT name={name} result={result}")
        if SHOW_TOOL_RESULTS:
            print(f"{TOOL_COLOR}🛠  Tool result: {result}{RESET}")
        return result
    except Exception as e:
        err = f"Error executing tool '{name}': {e}"
        logger.error(err)
        print(f"{TOOL_COLOR}⚠️  {err}{RESET}")
        return err

def process_history(history):
    """
    Sends the conversation `history` to the model, executes any tool calls,
    and returns the updated history plus the assistant's text response.
    """
    while True:
        #logger.debug(f"LLM_REQUEST history={history}")
        resp = client.responses.create(
            model=MODEL_NAME,
            input=history,
            tools=[t for t in tool_schemas if not ENABLED_TOOLS or t['name'] in ENABLED_TOOLS],
            tool_choice="auto"
        )
        #logger.debug(f"LLM_RAW_RESPONSE {resp}")

        # Handle any function calls the model wants to make
        calls = [c for c in getattr(resp, 'output', []) if getattr(c, 'type', None) == 'function_call']
        if calls:
            for call in calls:
                args = json.loads(call.arguments)
                if ENABLED_TOOLS and call.name not in ENABLED_TOOLS:
                    continue
                result = call_tool(call.name, args)
                history.append({
                    'type': 'function_call',
                    'name': call.name,
                    'arguments': call.arguments,
                    'call_id': call.call_id
                })
                history.append({
                    'type': 'function_call_output',
                    'call_id': call.call_id,
                    'output': result
                })
            continue

        assistant_text = getattr(resp, 'output_text', '')
        #logger.debug(f"LLM_OUTPUT_TEXT {assistant_text}")
        history.append({'role': 'assistant', 'content': assistant_text})
        return history, assistant_text
