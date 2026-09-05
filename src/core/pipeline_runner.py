import os
import sys
import re
import time
from datetime import datetime
import agent_config as config
from src.utils.logger import logger
from src.fetchers.ieee_fetcher import fetch_ieee_papers
from src.fetchers.arxiv_fetcher import fetch_arxiv_papers
from src.fetchers.semantic_scholar_fetcher import fetch_semantic_scholar_papers
from src.fetchers.citation_enricher import enrich_literature_review
from src.utils.pdf_downloader import download_pdfs
from src.auth import (
    prompt_auth_instructions_if_needed,
    COOKIES_FILE_PATH,
    load_ezproxy_cookies,
    verify_live_ieee_access,
    EZProxyManager,
)
from src.agents.sub_agents import (
    analyze_kinematic,
    analyze_physics_diffusion,
    analyze_rl_control,
    analyze_pose_vision,
)
from src.agents.orchestrator import synthesize_literature_review


def build_auth_required_message(reason: str, query: str = "") -> str:
    """
    Constructs a clear, end-user friendly Markdown message when institutional
    authentication is missing or expired, preventing token wastage.
    """
    return (
        "# 🛑 IEEE Xplore Institutional Access Required\n\n"
        "The research pipeline was **halted early to preserve your LLM tokens**, "
        "because fetching and synthesizing full-text peer-reviewed IEEE publications requires active institutional access.\n\n"
        "### 🔍 Access Verification Details:\n"
        f"- **Reason:** `{reason}`\n"
        f"- **Research Query:** `{query[:120]}`\n"
        "- **Session Status:** ❌ Session cookies are missing, invalid, or expired\n\n"
        "---\n\n"
        "### 💡 How to Proceed (Choose one option):\n\n"
        "#### Option 1: Trigger Automated Browser 2FA Login in Chat\n"
        "Type `/login` in OpenWebUI chat. The agent will launch the browser workflow, send a push notification to your phone, and return here once approved.\n\n"
        "#### Option 2: Provide Session Cookies in OpenWebUI (Fastest if already logged in)\n"
        "1. In your browser where IEEE Xplore is already logged in (shows *Access provided by: Afeka College*):\n"
        "2. Copy your active cookies (`F12 ➔ Application ➔ Cookies` or `Cookie-Editor` extension).\n"
        "3. In OpenWebUI, open pipeline settings (⚙️ **Valves**).\n"
        "4. Paste into **`EZPROXY_COOKIE`** and save.\n"
        "5. Resubmit your research prompt!\n\n"
        "#### Option 3: Run Authenticator on Server\n"
        "In your server terminal, execute:\n"
        "```bash\n"
        "python3 -m src.auth.ezproxy_session\n"
        "```\n"
        "*(Approve the fingerprint push notification on your mobile phone)*.\n"
    )


def extract_core_keywords(query: str) -> str:
    """
    Sanitizes user prompt. If the user passes a long detailed instruction prompt
    in OpenWebUI, this extracts clean academic search terms so search APIs don't fail.
    """
    if not query or not query.strip():
        return config.DEFAULT_SEARCH_QUERY

    cleaned = query.strip()
    words = cleaned.split()
    
    if len(words) <= 6 and not any(w in cleaned.lower() for w in ["perform", "review", "dimension"]):
        return cleaned

    cleaned_lower = cleaned.lower()
    meta_phrases = [
        "perform a comprehensive academic literature review on",
        "perform a literature review on",
        "write a literature review on",
        "focus on peer-reviewed ieee publications",
        "analyze and evaluate across the following four core dimensions",
        "synthesize the findings into a structured review"
    ]
    for mp in meta_phrases:
        cleaned_lower = cleaned_lower.replace(mp, "")

    core_terms = []
    if "text-to-motion" in cleaned_lower or "text to motion" in cleaned_lower or "motion synthesis" in cleaned_lower:
        core_terms.append("text-to-motion")
    if "physics" in cleaned_lower or "diffusion" in cleaned_lower:
        core_terms.append("physics diffusion")
    if "reinforcement learning" in cleaned_lower or "rl" in cleaned_lower or "control" in cleaned_lower:
        core_terms.append("reinforcement learning")
    if "smpl" in cleaned_lower or "pose" in cleaned_lower or "mediapipe" in cleaned_lower:
        core_terms.append("3d pose estimation")

    if core_terms:
        return " ".join(core_terms)

    clean_words = [w for w in re.sub(r'[^a-zA-Z0-9\s-]', '', cleaned_lower).split() if len(w) > 2]
    return " ".join(clean_words[:5]) if clean_words else config.DEFAULT_SEARCH_QUERY


def execute_t2m_research(
    query: str = config.DEFAULT_SEARCH_QUERY,
    enable_ieee: bool = config.ENABLE_IEEE_DEFAULT,
    enable_scholar: bool = config.ENABLE_SCHOLAR_DEFAULT,
    enable_arxiv: bool = config.ENABLE_ARXIV_DEFAULT,
    enable_semantic_scholar: bool = config.ENABLE_SEMANTIC_SCHOLAR_DEFAULT,
    max_results_per_domain: int = config.MAX_RESULTS_PER_DOMAIN,
    ezproxy_cookie: str = "",
    ezproxy_domain: str = config.EZPROXY_DOMAIN_DEFAULT,
    kinematic_prompt: str = None,
    physics_prompt: str = None,
    rl_prompt: str = None,
    pose_prompt: str = None,
    orchestrator_prompt: str = None,
    save_output_file: bool = True,
    auto_sso_login: bool = config.AUTO_SSO_LOGIN_DEFAULT,
    status_callback: callable = None,
    output_filename: str = config.DEFAULT_OUTPUT_FILE,
) -> str:
    """
    Central core execution engine for T2M Research Agent.
    Used by both CLI (main.py) and Open WebUI Pipeline (t2m_pipeline.py).
    Strictly adheres to active fetcher flags.
    Supports automated mobile push SSO authentication and real-time status callbacks.
    Enforces strict Fail-Fast token preservation if institutional access is required but unauthenticated.
    """
    clean_query = extract_core_keywords(query)

    logger.info("==================================================")
    logger.info("🚀 Starting T2M Research Framework Engine")
    logger.info(f"[*] Raw Prompt Length: {len(query)} chars")
    logger.info(f"[*] Extracted Search Query: '{clean_query}'")
    logger.info(f"[*] Active Fetchers -> IEEE: {enable_ieee} | ArXiv: {enable_arxiv} | Scholar: {enable_scholar} | Semantic Scholar: {enable_semantic_scholar}")
    logger.info("==================================================\n")

    if ezproxy_cookie.strip():
        os.environ["EZPROXY_COOKIE"] = ezproxy_cookie.strip()
        logger.info("[*] Using EZproxy cookie provided via Valves configuration.")

    manager = EZProxyManager(cookie_override=ezproxy_cookie)

    # 🛡️ LIVE HEALTH-CHECK & AUTOMATED SSO FALLBACK:
    if enable_ieee:
        logger.info("[*] Performing Live Health-Check on IEEE institutional access...")
        if status_callback:
            status_callback("🔍 Verifying IEEE institutional access...")

        is_authed, reason = manager.ensure_valid_session(
            auto_login=auto_sso_login,
            status_callback=status_callback,
        )

        if not is_authed:
            logger.warning(f"🛑 [FAIL-FAST] IEEE Authentication check failed: {reason}")
            logger.warning("🛑 Halting execution to preserve search quotas and LLM tokens.\n")
            return build_auth_required_message(reason, query=query)

        logger.info(f"✅ [HEALTH-CHECK OK] {reason}\n")
    elif enable_scholar or enable_semantic_scholar:
        prompt_auth_instructions_if_needed()

    # Precise domain search terms (short queries first)
    domains = {
        "kinematic": [
            "text to motion kinematics",
            "kinematic human motion generation",
            "SMPL motion synthesis"
        ],
        "physics": [
            "physics guided motion diffusion",
            "physics contact motion generation",
            "foot sliding mitigation motion"
        ],
        "rl": [
            "reinforcement learning motion control",
            "reinforcement learning humanoid control",
            "physics character control RL"
        ],
        "pose": [
            "3d human pose estimation SMPL",
            "monocular pose estimation human",
            "MediaPipe 3d pose motion"
        ],
    }

    # 1. FETCH PAPERS
    def fetch_papers_for_domain(domain_key: str):
        papers = []
        query_terms = domains.get(domain_key, [clean_query])
        
        for term in query_terms:
            time.sleep(1.2)
            if enable_ieee:
                res = fetch_ieee_papers(term, max_results=max_results_per_domain, ezproxy_domain=ezproxy_domain)
                if res:
                    papers.extend(res)
            if enable_arxiv and len(papers) < max_results_per_domain:
                res = fetch_arxiv_papers(term, max_results=max_results_per_domain)
                if res:
                    papers.extend(res)
            if enable_semantic_scholar and len(papers) < max_results_per_domain:
                res = fetch_semantic_scholar_papers(term, max_results=max_results_per_domain)
                if res:
                    papers.extend(res)
                    
            if len(papers) >= max_results_per_domain:
                break
                
        return papers[:max_results_per_domain]

    logger.info("[1/4] Fetching papers across selected sources...")
    kinematic_papers = fetch_papers_for_domain("kinematic")
    physics_papers = fetch_papers_for_domain("physics")
    rl_papers = fetch_papers_for_domain("rl")
    pose_papers = fetch_papers_for_domain("pose")

    all_papers_raw = kinematic_papers + physics_papers + rl_papers + pose_papers
    unique_papers = []
    seen_keys = set()

    for p in all_papers_raw:
        paper_key = p.get('url') or p.get('title')
        if paper_key not in seen_keys:
            seen_keys.add(paper_key)
            unique_papers.append(p)

    logger.info(f"\n[*] Analytics: Fetched {len(all_papers_raw)} total hits across enabled fetchers.")
    logger.info(f"[*] Deduped: Found {len(unique_papers)} UNIQUE papers across all domains.")

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    articles_dir = os.path.join(project_root, "articles")

    # 2. DOWNLOAD PDFs
    logger.info("\n[2/4] Downloading UNIQUE PDFs for Deep RAG ingestion...")
    download_count = download_pdfs(
        unique_papers,
        output_dir=articles_dir,
        session=manager.get_session(),
        cookie_override=ezproxy_cookie
    )

    # 3. SUB-AGENTS ANALYSIS
    logger.info("\n[3/4] Engaging AI Expert Sub-Agents...")
    kinematic_result = analyze_kinematic(kinematic_papers, custom_prompt=kinematic_prompt)
    physics_result = analyze_physics_diffusion(physics_papers, custom_prompt=physics_prompt)
    rl_result = analyze_rl_control(rl_papers, custom_prompt=rl_prompt)
    pose_result = analyze_pose_vision(pose_papers, custom_prompt=pose_prompt)

    # 4. MASTER ORCHESTRATOR SYNTHESIS
    logger.info("\n[4/4] Engaging Master Orchestrator for literature synthesis...")
    final_review = synthesize_literature_review(
        kinematic_result,
        physics_result,
        rl_result,
        pose_result,
        custom_prompt=orchestrator_prompt
    )

    # Build response for Open WebUI & File Saving
    summary_header = (
        f"# 🎓 T2M Academic Research Report\n\n"
        f"**Query:** `{query[:100]}...` | **Extracted Search Terms:** `{clean_query}` | **Unique Papers Processed:** {len(unique_papers)} | **PDFs Secured:** {download_count}\n"
        f"**Fetchers Active:** "
        f"{'IEEE ' if enable_ieee else ''}"
        f"{'GoogleScholar ' if enable_scholar else ''}"
        f"{'ArXiv ' if enable_arxiv else ''}"
        f"{'SemanticScholar ' if enable_semantic_scholar else ''}\n\n"
        f"---\n\n"
        f"## 🔍 Intermediate Sub-Agent Findings (Tables & Analysis)\n\n"
        f"### 1. Kinematic Models Sub-Agent\n{kinematic_result}\n\n"
        f"### 2. Physics & Diffusion Sub-Agent\n{physics_result}\n\n"
        f"### 3. RL Control Sub-Agent\n{rl_result}\n\n"
        f"### 4. Pose & Vision Sub-Agent\n{pose_result}\n\n"
        f"---\n\n"
        f"# 🏛️ Master Literature Synthesis (Orchestrator)\n\n"
        f"{final_review}"
    )

    # 4. ACADEMIC CREDIBILITY & PEER-REVIEW ENRICHMENT
    if unique_papers:
        if status_callback:
            status_callback("📊 Enriching review with CrossRef and ArXiv peer-review verification...")
        summary_header = enrich_literature_review(summary_header, papers=unique_papers)

    if save_output_file:
        output_path = os.path.join(project_root, output_filename)
        try:
            st = os.stat(project_root)
            host_uid, host_gid = st.st_uid, st.st_gid
        except Exception:
            host_uid, host_gid = 1000, 1000

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(summary_header)
            try:
                os.chown(output_path, host_uid, host_gid)
                os.chmod(output_path, 0o666)
            except Exception:
                pass
            logger.info(f"✅ Review file saved to: {output_path}")
        except Exception as e:
            logger.error(f"[!] Failed to write review file {output_path}: {e}")

    return summary_header


if __name__ == "__main__":
    print("==================================================")
    print("🔬 Pipeline Runner Standalone Health Check")
    print("==================================================")
    manager = EZProxyManager()
    status = manager.check_status()
    print(f"[*] Auth Status: {status['message']}")
    print("==================================================")
