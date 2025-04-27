# config.py
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load .env into environment
load_dotenv()

API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_API_KEY = os.getenv(API_KEY_ENV)
if not OPENAI_API_KEY:
    raise RuntimeError(f"Please set the {API_KEY_ENV} environment variable")

# Configurable parameters
MODEL_NAME = os.getenv("MODEL_NAME", "o4-mini")
PROMPT_NAME = os.getenv("PROMPT_NAME", "default_prompt.txt")

# Enable all tools except partial editing, edit by string, and shell
ENABLED_TOOLS = os.getenv("ENABLED_TOOLS", "edit_file,read_codebase,calculate,create_file,read_files,git").split(",")
ENABLED_TOOLS = [t.strip() for t in ENABLED_TOOLS if t.strip()]

# Toggle showing tool call and arguments
SHOW_TOOL_CALLS = os.getenv("SHOW_TOOL_CALLS", "true").lower() == "true"

# Toggle showing tool call results
SHOW_TOOL_RESULTS = os.getenv("SHOW_TOOL_RESULTS", "false").lower() == "true"

# Toggle showing the system prompt in CLI
SHOW_SYSTEM_PROMPT = True

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)