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
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
PROMPT_PATH = os.getenv("PROMPT_PATH", "prompts/default_prompt.txt")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)
