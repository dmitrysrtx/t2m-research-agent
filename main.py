import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.pipeline_runner import execute_t2m_research

def main():
    # CLI entry point runs core pipeline engine
    result = execute_t2m_research(
        query="text-to-motion human motion",
        enable_ieee=True,
        enable_arxiv=False,
        enable_scholar=False,
        enable_semantic_scholar=False,
        max_results_per_domain=5,
        save_output_file=True
    )
    
    if "🛑" in result:
        print(result)
        return
        
    # Run OpenAlex Enrichment if script exists
    enrich_script = os.path.join(PROJECT_ROOT, "enrich_review.py")
    if os.path.exists(enrich_script):
        os.system(f"python3 {enrich_script}")

if __name__ == "__main__":
    main()
