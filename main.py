import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.pipeline_runner import execute_t2m_research
import config

def main():
    # CLI entry point runs core pipeline engine using SSOT configuration
    result = execute_t2m_research(
        query=config.DEFAULT_SEARCH_QUERY,
        enable_ieee=config.ENABLE_IEEE_DEFAULT,
        enable_scholar=config.ENABLE_SCHOLAR_DEFAULT,
        enable_arxiv=config.ENABLE_ARXIV_DEFAULT,
        enable_semantic_scholar=config.ENABLE_SEMANTIC_SCHOLAR_DEFAULT,
        max_results_per_domain=config.MAX_RESULTS_PER_DOMAIN,
        save_output_file=True
    )
    
    if "🛑" in result:
        print(result)
        return
if __name__ == "__main__":
    main()
