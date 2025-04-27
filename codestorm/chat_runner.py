import json
import os
import logging
from .config import client, MODEL_NAME, SHOW_TOOL_CALLS, SHOW_TOOL_RESULTS, ENABLED_TOOLS
from .tools import tools as tool_schemas, TOOL_MAP

# Setup logging to file
log_file = os.path.join(os.getcwd(), 'codestorm.log')
logger = logging.getLogger('codestorm')
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def call_tool(name, args):
    """
    Safely call the specified tool with arguments, catching exceptions.
    """
    logger.debug(f"TOOL_CALL name={name} args={args}")
    try:
        func = TOOL_MAP.get(name)
        if not func:
            msg = f"Error: Unknown tool '{name}'"
            logger.error(msg)
            return msg
        result = func(**args)
        logger.debug(f"TOOL_RESULT name={name} result={result}")
        return result
    except Exception as e:
        err = f"Error executing tool '{name}': {e}"
        logger.error(err)
        return err


def process_history(history):
    """
    Sends the conversation `history` to the model, executes any tool calls,
    and returns the updated history plus the assistant's text response.
    Automatically preloads environment context (codebase tree, README, git diff)
    before the first LLM invocation.
    """
    # Preload context on first call
    if not any(item.get('type') == 'function_call' for item in history):
        initial_tools = [
            ('read_codebase', {}),
            ('read_files', {'file_list': 'README.md'}),
            ('git', {'command': 'diff'})
        ]
        for idx, (tool_name, tool_args) in enumerate(initial_tools, start=1):
            if SHOW_TOOL_CALLS:
                print(f"Tool call: {tool_name}({tool_args})")
            result = call_tool(tool_name, tool_args)
            if SHOW_TOOL_RESULTS:
                print(f"Tool result: {result}")
            history.append({
                'type': 'function_call',
                'name': tool_name,
                'arguments': json.dumps(tool_args),
                'call_id': f'init_{idx}'
            })
            history.append({
                'type': 'function_call_output',
                'call_id': f'init_{idx}',
                'output': result
            })

    while True:
        logger.debug(f"LLM_REQUEST history={history}")
        resp = client.responses.create(
            model=MODEL_NAME,
            input=history,
            tools=[t for t in tool_schemas if not ENABLED_TOOLS or t['name'] in ENABLED_TOOLS],
            tool_choice="auto"
        )
        logger.debug(f"LLM_RAW_RESPONSE {resp}")

        # Collect any function calls the model wants to make
        tool_calls = [c for c in resp.output if getattr(c, 'type', None) == 'function_call']
        if tool_calls:
            logger.debug(f"LLM_TOOL_CALLS {tool_calls}")
            for call in tool_calls:
                args = json.loads(call.arguments)
                if ENABLED_TOOLS and call.name not in ENABLED_TOOLS:
                    continue
                if SHOW_TOOL_CALLS:
                    print(f"Tool call: {call.name}({args})")

                result = call_tool(call.name, args)

                if SHOW_TOOL_RESULTS:
                    print(f"Tool result: {result}")
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

        assistant_text = resp.output_text
        logger.debug(f"LLM_OUTPUT_TEXT {assistant_text}")
        history.append({'role': 'assistant', 'content': assistant_text})
        return history, assistant_text