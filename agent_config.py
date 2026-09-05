import os
from dotenv import load_dotenv

# Path resolution: repo root is the directory containing this file
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# ==============================================================================
# LLM Provider Configuration
# ==============================================================================
API_KEY = os.getenv("OPENROUTER_API_KEY", "")
BASE_URL = os.getenv("API_BASE_URL", "https://openrouter.ai/api/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "anthropic/claude-3.5-sonnet")

# ==============================================================================
# Academic Search & Fetcher Defaults (Single Source of Truth)
# ==============================================================================
DEFAULT_SEARCH_QUERY = os.getenv("DEFAULT_SEARCH_QUERY", "text-to-motion human motion")
MAX_RESULTS_PER_DOMAIN = int(os.getenv("MAX_RESULTS_PER_DOMAIN", "5"))

ENABLE_IEEE_DEFAULT = os.getenv("ENABLE_IEEE", "True").lower() == "true"
ENABLE_SCHOLAR_DEFAULT = os.getenv("ENABLE_SCHOLAR", "True").lower() == "true"
ENABLE_ARXIV_DEFAULT = os.getenv("ENABLE_ARXIV", "False").lower() == "true"
ENABLE_SEMANTIC_SCHOLAR_DEFAULT = os.getenv("ENABLE_SEMANTIC_SCHOLAR", "False").lower() == "true"

DEFAULT_OUTPUT_FILE = os.getenv("DEFAULT_OUTPUT_FILE", "LITERATURE_REVIEW.md")

# ==============================================================================
# Institutional & EZproxy Defaults
# ==============================================================================
EZPROXY_DOMAIN_DEFAULT = os.getenv("EZPROXY_DOMAIN", "ezproxy.afeka.ac.il")
AUTO_SSO_LOGIN_DEFAULT = os.getenv("AUTO_SSO_LOGIN", "True").lower() == "true"
IEEE_INSTITUTION_DEFAULT = os.getenv("IEEE_INSTITUTION", "afeka")


if __name__ == "__main__":
    print("==================================================")
    print("⚙️ Configuration (Single Source of Truth)")
    print("==================================================")
    print(f"[*] Model: {MODEL_NAME}")
    print(f"[*] Base URL: {BASE_URL}")
    print(f"[*] API Key Present: {'Yes' if API_KEY else 'No'}")
    print(f"[*] Search Query Default: {DEFAULT_SEARCH_QUERY}")
    print(f"[*] Max Results Per Domain: {MAX_RESULTS_PER_DOMAIN}")
    print(f"[*] Fetchers -> IEEE: {ENABLE_IEEE_DEFAULT} | Scholar: {ENABLE_SCHOLAR_DEFAULT} | ArXiv: {ENABLE_ARXIV_DEFAULT} | Semantic: {ENABLE_SEMANTIC_SCHOLAR_DEFAULT}")
    print(f"[*] Output Report: {DEFAULT_OUTPUT_FILE}")
    print(f"[*] Institution: {IEEE_INSTITUTION_DEFAULT} ({EZPROXY_DOMAIN_DEFAULT})")
    print(f"[*] Auto 2FA SSO: {AUTO_SSO_LOGIN_DEFAULT}")
    print("==================================================")
