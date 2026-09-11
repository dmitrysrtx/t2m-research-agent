import os
from src.core.config_loader import cfg

# Path resolution: repo root is the directory containing this file
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# ==============================================================================
# 1. LLM Provider Configuration
# ==============================================================================
API_KEY = cfg.get("llm.api_key") or os.getenv("OPENROUTER_API_KEY", "")
BASE_URL = cfg.get("llm.base_url") or os.getenv("API_BASE_URL", "https://openrouter.ai/api/v1")
MODEL_NAME = cfg.get("llm.model_name") or os.getenv("MODEL_NAME", "anthropic/claude-3.5-sonnet")
SUBAGENT_TEMPERATURE = float(cfg.get("llm.subagent_temperature", 0.2))
ORCHESTRATOR_TEMPERATURE = float(cfg.get("llm.orchestrator_temperature", 0.3))
SUBAGENT_MAX_TOKENS = int(cfg.get("llm.subagent_max_tokens", 4096))
ORCHESTRATOR_MAX_TOKENS = int(cfg.get("llm.orchestrator_max_tokens", 8192))

# ==============================================================================
# 2. Academic Search & Discovery Layer
# ==============================================================================
DEFAULT_SEARCH_QUERY = cfg.get("search_discovery.default_query", "text-to-motion human motion")
MAX_RESULTS_PER_DOMAIN = int(cfg.get("search_discovery.max_results_per_domain", 5))
ENABLE_IEEE_DEFAULT = bool(cfg.get("search_discovery.enable_ieee", False))
ENABLE_SCHOLAR_DEFAULT = bool(cfg.get("search_discovery.enable_scholar", True))
ENABLE_ARXIV_DEFAULT = bool(cfg.get("search_discovery.enable_arxiv", False))
ENABLE_SEMANTIC_SCHOLAR_DEFAULT = bool(cfg.get("search_discovery.enable_semantic_scholar", False))
SEMANTIC_SCHOLAR_API_KEY = cfg.get("search_discovery.semantic_scholar_api_key", "")
SEMANTIC_SCHOLAR_MIN_CITATIONS = int(cfg.get("search_discovery.min_citations", 0))
SEMANTIC_SCHOLAR_FIELDS_OF_STUDY = cfg.get("search_discovery.fields_of_study", "Computer Science,Engineering")

# ==============================================================================
# 3. Dual-Bucket Ranking & Scoring Formulas
# ==============================================================================
FRONTIER_BUCKET_RATIO = float(cfg.get("scoring_ranking.frontier_bucket_ratio", 0.65))
FOUNDATIONAL_BUCKET_RATIO = float(cfg.get("scoring_ranking.foundational_bucket_ratio", 0.35))
RECENT_YEAR_WINDOW = int(cfg.get("scoring_ranking.recent_year_window", 2))
INFLUENTIAL_CITATION_WEIGHT = float(cfg.get("scoring_ranking.influential_citation_weight", 2.5))
TIME_DELTA_MIN = float(cfg.get("scoring_ranking.time_delta_min", 0.5))
VENUE_TIER_1_WEIGHT = float(cfg.get("scoring_ranking.venue_tier_1_weight", 2.0))
VENUE_TIER_2_WEIGHT = float(cfg.get("scoring_ranking.venue_tier_2_weight", 1.35))
VENUE_TIER_3_WEIGHT = float(cfg.get("scoring_ranking.venue_tier_3_weight", 1.0))
CODE_ARTIFACT_SCORE_BOOST = float(cfg.get("scoring_ranking.verified_code_boost", 35.0))

# ==============================================================================
# 4. Artifact & GitHub Code Verification ("Code-First" Mode)
# ==============================================================================
REQUIRE_CODE_DEFAULT = bool(cfg.get("code_artifacts.require_code", False))
PREFER_CODE_DEFAULT = bool(cfg.get("code_artifacts.prefer_code", True))
GITHUB_MAX_WORKERS = int(cfg.get("code_artifacts.github_max_workers", 8))
GITHUB_CONNECT_TIMEOUT = float(cfg.get("code_artifacts.github_connect_timeout", 2.0))
GITHUB_READ_TIMEOUT = float(cfg.get("code_artifacts.github_read_timeout", 3.0))

# ==============================================================================
# 5. PDF Acquisition & Ingestion Cascade
# ==============================================================================
TARGET_PDF_COUNT = int(cfg.get("pdf_ingestion.target_pdf_count", 20))
CANDIDATE_POOL_MULTIPLIER = float(cfg.get("pdf_ingestion.candidate_pool_multiplier", 1.5))
ARTICLES_OUTPUT_DIR = cfg.get("pdf_ingestion.output_dir", "articles")
EZPROXY_DOMAIN_DEFAULT = cfg.get("pdf_ingestion.ezproxy_domain", "ezproxy.afeka.ac.il")
AUTO_SSO_LOGIN_DEFAULT = bool(cfg.get("pdf_ingestion.auto_sso_login", True))
IEEE_INSTITUTION_DEFAULT = cfg.get("pdf_ingestion.ieee_institution", "afeka")
UNPAYWALL_EMAIL = cfg.get("pdf_ingestion.unpaywall_email", "academic_bot@afeka.ac.il")
PDF_DOWNLOAD_TIMEOUT = int(cfg.get("pdf_ingestion.download_timeout", 25))
PDF_MAX_SIZE_MB = int(cfg.get("pdf_ingestion.max_file_size_mb", 50))
CLEAR_ARTICLES_DIR = bool(cfg.get("pdf_ingestion.clear_articles_dir", False))

# ==============================================================================
# 6. Telemetry, Storage & Observability
# ==============================================================================
DEFAULT_OUTPUT_FILE = cfg.get("telemetry_output.default_output_file", "LITERATURE_REVIEW.md")
ENABLE_CLI_LOGS = bool(cfg.get("telemetry_output.enable_cli_logs", True))
LANGFUSE_HOST = cfg.get("telemetry_output.langfuse_host", "http://192.168.68.53:3005")
LANGFUSE_PUBLIC_KEY = cfg.get("telemetry_output.langfuse_public_key", "")
LANGFUSE_SECRET_KEY = cfg.get("telemetry_output.langfuse_secret_key", "")


if __name__ == "__main__":
    print("==================================================")
    print(f"⚙️ Configuration (Single Source of Truth via cfg, Profile: {cfg.get_profile()})")
    print("==================================================")
    print(f"[*] Model: {MODEL_NAME}")
    print(f"[*] Base URL: {BASE_URL}")
    print(f"[*] API Key Present: {'Yes' if API_KEY else 'No'}")
    print(f"[*] Search Query Default: {DEFAULT_SEARCH_QUERY}")
    print(f"[*] Max Results Per Domain: {MAX_RESULTS_PER_DOMAIN}")
    print(f"[*] Fetchers -> IEEE: {ENABLE_IEEE_DEFAULT} | Scholar: {ENABLE_SCHOLAR_DEFAULT} | ArXiv: {ENABLE_ARXIV_DEFAULT} | Semantic: {ENABLE_SEMANTIC_SCHOLAR_DEFAULT}")
    print(f"[*] SOTA Ratio: {FRONTIER_BUCKET_RATIO} | Foundational Ratio: {FOUNDATIONAL_BUCKET_RATIO}")
    print(f"[*] Code-First -> Require: {REQUIRE_CODE_DEFAULT} | Prefer: {PREFER_CODE_DEFAULT} (Boost: {CODE_ARTIFACT_SCORE_BOOST})")
    print(f"[*] Output Report: {DEFAULT_OUTPUT_FILE}")
    print(f"[*] Institution: {IEEE_INSTITUTION_DEFAULT} ({EZPROXY_DOMAIN_DEFAULT})")
    print(f"[*] Auto 2FA SSO: {AUTO_SSO_LOGIN_DEFAULT}")
    print(f"[*] CLI Logs: {ENABLE_CLI_LOGS}")
    print(f"[*] Langfuse Host: {LANGFUSE_HOST} (Active: {'Yes' if LANGFUSE_PUBLIC_KEY else 'No'})")
    print("==================================================")
