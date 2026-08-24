import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# We use an OpenAI API-compatible client.
# Based on your setup, it defaults to OpenRouter, but can be configured via .env.

API_KEY = os.getenv("OPENROUTER_API_KEY", "")
BASE_URL = os.getenv("API_BASE_URL", "https://openrouter.ai/api/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "anthropic/claude-3.5-sonnet")

# Limits for searching
MAX_PAPERS_PER_CATEGORY = 5
