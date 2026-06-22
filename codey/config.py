# config.py
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_API_KEY = os.getenv(API_KEY_ENV)
OPENAI_BASE_URL = "https://openrouter.ai/api/v1"
if not OPENAI_API_KEY:
    raise RuntimeError(f"Please set the {API_KEY_ENV} environment variable")

PERSONAS = {
    "gpt-5": {"model": os.getenv("UNLOCKED_MODEL", "minimax/minimax-m3"), "prompt": "codey-unlocked.txt"},
}

DEFAULT_PERSONA = os.getenv("DEFAULT_PERSONA", "gpt-5")

MODEL_NAME  = PERSONAS.get(DEFAULT_PERSONA, PERSONAS["gpt-5"])["model"]
PROMPT_NAME = PERSONAS.get(DEFAULT_PERSONA, PERSONAS["gpt-5"])["prompt"]

ENABLED_TOOLS = os.getenv(
    "ENABLED_TOOLS",
    "ask,shell,terminal,delegate,web,read_codebase,read_files,view_image,calculate,create_file,edit_file,git,grep"
).split(",")
ENABLED_TOOLS = [t.strip() for t in ENABLED_TOOLS if t.strip()]

SHOW_TOOL_CALLS   = os.getenv("SHOW_TOOL_CALLS", "true").lower() == "true"
SHOW_TOOL_RESULTS = os.getenv("SHOW_TOOL_RESULTS", "false").lower() == "true"
SHOW_SYSTEM_PROMPT = True

# Prompt the user to approve shell commands before they run (set CONFIRM_SHELL=true)
CONFIRM_SHELL = os.getenv("CONFIRM_SHELL", "false").lower() == "true"

# Maximum tool-call rounds per user turn; prevents runaway loops
MAX_TOOL_ROUNDS = int(os.getenv("MAX_TOOL_ROUNDS", "25"))

client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
