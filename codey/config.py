# config.py
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load .env into environment
load_dotenv()

API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_API_KEY = os.getenv(API_KEY_ENV)
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")  # Optional custom base URL
if not OPENAI_API_KEY:
    raise RuntimeError(f"Please set the {API_KEY_ENV} environment variable")

# Persona selection
PERSONAS = {
    "collaborator": {"model": os.getenv("COLLABORATOR_MODEL", "gpt-4.1-mini"), "prompt": "default_prompt.txt"},
    "qwen": {"model": os.getenv("UNLOCKED_MODEL", "qwen/qwen3-coder"), "prompt": "codey-unlocked.txt"},
    "deepseek": {"model": os.getenv("UNLOCKED_MODEL", "deepseek/deepseek-chat-v3-0324"), "prompt": "codey-unlocked.txt"},
    "claude": {"model": os.getenv("UNLOCKED_MODEL", "anthropic/claude-sonnet-4"), "prompt": "codey-unlocked.txt"},
    "gpt-5": {"model": os.getenv("UNLOCKED_MODEL", "openai/gpt-5"), "prompt": "codey-unlocked.txt"},
}

# Default persona
DEFAULT_PERSONA = os.getenv("DEFAULT_PERSONA", "gpt-5")

# Configurable parameters based on persona
MODEL_NAME = PERSONAS.get(DEFAULT_PERSONA, PERSONAS["gpt-5"])["model"]
PROMPT_NAME = PERSONAS.get(DEFAULT_PERSONA, PERSONAS["gpt-5"])["prompt"]

# Enable tools by default
# Previously excluded partial editing, string-based edit, and shell
ENABLED_TOOLS = os.getenv(
    "ENABLED_TOOLS",
    "read_codebase,read_files,calculate,create_file,edit_file,git,grep,shell"
).split(",")
ENABLED_TOOLS = [t.strip() for t in ENABLED_TOOLS if t.strip()]

# Toggle showing tool call and arguments
SHOW_TOOL_CALLS = os.getenv("SHOW_TOOL_CALLS", "true").lower() == "true"

# Toggle showing tool call results
SHOW_TOOL_RESULTS = os.getenv("SHOW_TOOL_RESULTS", "false").lower() == "true"

# Toggle showing the system prompt in CLI
SHOW_SYSTEM_PROMPT = True

# Initialize OpenAI client
if OPENAI_BASE_URL:
    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
else:
    client = OpenAI(api_key=OPENAI_API_KEY)
