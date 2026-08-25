import os
from src.utils.logger import logger
from src.fetchers.arxiv_fetcher import fetch_arxiv_papers
from src.agents.sub_agents import (
    analyze_kinematic, 
    analyze_physics_diffusion, 
    analyze_rl_control, 
    analyze_pose_vision
)
from src.agents.orchestrator import synthesize_literature_review
from src.utils.pdf_downloader import download_pdfs

def main():
    logger.info("==================================================")
    logger.info("🚀 Starting T2M Multi-Agent Research Framework")
    logger.info("==================================================\n")

    # 1. FETCHING DATA
    logger.info("[1/4] Fetching latest research papers (ArXiv Reliable Pool)...")
    
    kinematic_papers = fetch_arxiv_papers("text-to-motion generative", max_results=15)
    physics_diff_papers = fetch_arxiv_papers("physics human motion generation", max_results=15)
    rl_papers = fetch_arxiv_papers("reinforcement learning character animation physics", max_results=15)
    pose_papers = fetch_arxiv_papers("3d human pose estimation mediapipe smpl", max_results=15)

    all_papers_raw = kinematic_papers + physics_diff_papers + rl_papers + pose_papers
    
    # Deduplicate for accurate counting and efficient downloading
    unique_papers = []
    seen_urls = set()
    for p in all_papers_raw:
        if p['url'] not in seen_urls:
            seen_urls.add(p['url'])
            unique_papers.append(p)

    logger.info(f"\n[*] Analytics: Fetched {len(all_papers_raw)} total categorization hits.")
    logger.info(f"[*] Deduped: Found {len(unique_papers)} UNIQUE papers across all domains.")

    # 2. DOWNLOADING PDFs
    logger.info("\n[2/4] Downloading UNIQUE PDFs for Deep RAG ingestion...")
    download_pdfs(unique_papers, output_dir="articles")

    # 3. RUNNING SUB-AGENTS
    logger.info("\n[3/4] Engaging AI Expert Sub-Agents...")
    kinematic_result = analyze_kinematic(kinematic_papers)
    physics_diff_result = analyze_physics_diffusion(physics_diff_papers)
    rl_result = analyze_rl_control(rl_papers)
    pose_result = analyze_pose_vision(pose_papers)

    # 4. RUNNING MASTER ORCHESTRATOR
    logger.info("\n[4/4] Engaging Master Orchestrator for synthesis...")
    final_review = synthesize_literature_review(
        kinematic_result, 
        physics_diff_result, 
        rl_result, 
        pose_result
    )

    # 5. SAVING OUTPUT
    output_path = "LITERATURE_REVIEW.md"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# RAW DATA (Total Unique Papers processed: {len(unique_papers)})\n\n")
            f.write("## 1. Kinematic Models\n" + kinematic_result + "\n\n")
            f.write("## 2. Physics Diffusion\n" + physics_diff_result + "\n\n")
            f.write("## 3. RL Character Control\n" + rl_result + "\n\n")
            f.write("## 4. Pose Representation (MediaPipe/SMPL)\n" + pose_result + "\n\n")
            f.write("---\n\n")
            f.write("# MASTER LITERATURE REVIEW (Orchestrator Output)\n\n")
            f.write(final_review)
        logger.info(f"\n✅ Pipeline Complete! Initial review saved in: {output_path}")
        
        # 6. AUTO-ENRICHMENT STEP
        logger.info("\n[Auto-Step] Running OpenAlex Academic Enrichment...")
        os.system("python3 enrich_review.py")
        
    except Exception as e:
        logger.error(f"[!] Failed to write review file: {e}")

if __name__ == "__main__":
    main()
