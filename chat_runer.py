# chat_runner.py
import json
from config import client
from tools import tools as tool_schemas, TOOL_MAP

def call_tool(name, args):
    return TOOL_MAP[name](**args)

def process_history(history):
    """
    Sends the conversation `history` to the model, executes any tool calls,
    and returns the updated history plus the assistant’s text response.
    """
    while True:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=history,
            tools=tool_schemas,
            tool_choice="auto"
        )

        # Collect any function calls the model wants to make
        tool_calls = [c for c in resp.output if getattr(c, "type", None) == "function_call"]
        if tool_calls:
            for call in tool_calls:
                args = json.loads(call.arguments)
                result = call_tool(call.name, args)
                # Append the call and its output to history
                history.append({
                    "type": "function_call",
                    "name": call.name,
                    "arguments": call.arguments,
                    "call_id": call.call_id
                })
                history.append({
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": result
                })
            # Loop again so the model can consume the tool outputs
            continue

        # No more tool calls → this is the assistant’s final text reply
        assistant_text = resp.output_text
        history.append({"role": "assistant", "content": assistant_text})
        return history, assistant_text
