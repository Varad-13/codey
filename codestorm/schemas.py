# schemas.py
"""
Re-export tool schemas and mapping for use in chat_runner or elsewhere.
"""
from tools import tools as tool_schemas, TOOL_MAP

# list of JSON schemas for model tooling
tools = tool_schemas

# mapping of tool names to callable functions
tool_map = TOOL_MAP
