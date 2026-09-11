import os
import sys
import re
import time
from typing import Optional
from datetime import datetime
import agent_config as config
from src.utils.logger import logger
from src.telemetry import get_telemetry, TelemetryManager
from src.fetchers.ieee_fetcher import fetch_ieee_papers
from src.fetchers.scholar_fetcher import fetch_google_scholar_papers
from src.fetchers.arxiv_fetcher import fetch_arxiv_papers
from src.fetchers.semantic_scholar_fetcher import fetch_semantic_scholar_papers
from src.fetchers.citation_enricher import enrich_literature_review
from src.fetchers.github_finder import enrich_papers_with_github, resolve_paper_github
from src.utils.text_formatters import clean_github_markdown_link
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
        "perform a comprehensive literature review on",
        "perform a literature review on",
        "conduct a comprehensive literature review on",
        "conduct a literature review on",
        "write a comprehensive literature review on",
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

    meta_words = {"perform", "write", "conduct", "review", "literature", "academic", "comprehensive", "dimensions", "focus"}
    clean_words = [w for w in re.sub(r'[^a-zA-Z0-9\s-]', '', cleaned_lower).split() if len(w) > 2 and w.lower() not in meta_words]
    return " ".join(clean_words[:5]) if clean_words else config.DEFAULT_SEARCH_QUERY


def sanitize_markdown_table_github_urls(table_text: str, verified_urls: set) -> str:
    """Enforces that only verified GitHub URLs appear in tables, replacing dead/hallucinated links with N/A."""
    if not table_text:
        return table_text
    clean_verified = {u.rstrip("/").lower() for u in verified_urls if u and u != "N/A"}

    def _replace_link(match):
        full_text = match.group(0)
        url = match.group(2).rstrip("/").lower()
        if url.startswith("https://github.com/") and url not in clean_verified:
            return "N/A"
        return full_text

    sanitized = re.sub(r'\[([^\]]+)\]\((https?://github\.com/[^\)\s]+)\)', _replace_link, table_text)
    return clean_github_markdown_link(sanitized)


def build_unsecured_appendix(unsecured_list: list) -> str:
    """Builds an Appendix table for candidate papers whose full text could not be downloaded."""
    if not unsecured_list:
        return ""
    lines = [
        "## 📎 Appendix: Papers Identified via Citations (Full-Text Not Ingested)\n",
        "The following papers were identified and ranked during academic discovery, but their full-text PDF was paywalled or unavailable for deep ingestion:\n",
        "| Title (Year) | Venue | Citations | Code Repository | Ingestion Status |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]
    for p in unsecured_list:
        title = str(p.get("title", "Unknown Title")).replace("|", "-").strip()
        year = p.get("year") or "N/A"
        url = p.get("url") or "#"
        venue = p.get("venue") or "Academic Publication"
        citations = p.get("citations") or 0
        gh = clean_github_markdown_link(p.get("github_url") or "N/A")
        status = "Paywalled / Unavailable"
        lines.append(f"| [{title} ({year})]({url}) | {venue} | {citations} | {gh} | {status} |")
    return "\n".join(lines) + "\n\n"


def rank_and_filter_candidates(
    candidates: list,
    max_results: int,
    require_code: bool = False,
    prefer_code: bool = True,
    session: Optional[object] = None
) -> list:
    """
    Ranks candidates by code availability, citations, and influential citations.
    Enforces 'Code-First' selection according to require_code / prefer_code flags.
    """
    if not candidates:
        return []

    # 1. Concurrently resolve repositories for all candidate papers
    enrich_papers_with_github(candidates, session=session)

    for p in candidates:
        has_code = p.get("github_url") and p.get("github_url") != "N/A"
        boost = getattr(config, "CODE_ARTIFACT_SCORE_BOOST", 35.0) if has_code else 0.0
        cit = p.get("citations") or 0
        inf = p.get("influential_citations") or 0
        p["score"] = boost + cit + (inf * 2.0)

    if require_code:
        code_candidates = [p for p in candidates if p.get("github_url") and p.get("github_url") != "N/A"]
        if code_candidates:
            selected = sorted(code_candidates, key=lambda x: x.get("score", 0), reverse=True)
        else:
            logger.warning("[!] No code-bearing papers found for domain under require_code=True. Falling back to top cited papers.")
            selected = sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)
    elif prefer_code:
        selected = sorted(
            candidates,
            key=lambda x: (
                1 if (x.get("github_url") and x.get("github_url") != "N/A") else 0,
                x.get("score", 0)
            ),
            reverse=True
        )
    else:
        selected = sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)

    return selected[:max_results]


def execute_t2m_research(
    query: str = config.DEFAULT_SEARCH_QUERY,
    enable_ieee: bool = config.ENABLE_IEEE_DEFAULT,
    enable_scholar: bool = config.ENABLE_SCHOLAR_DEFAULT,
    enable_arxiv: bool = config.ENABLE_ARXIV_DEFAULT,
    enable_semantic_scholar: bool = config.ENABLE_SEMANTIC_SCHOLAR_DEFAULT,
    max_results_per_domain: int = config.MAX_RESULTS_PER_DOMAIN,
    require_code: bool = config.REQUIRE_CODE_DEFAULT,
    prefer_code: bool = config.PREFER_CODE_DEFAULT,
    ezproxy_cookie: str = "",
    ezproxy_domain: str = config.EZPROXY_DOMAIN_DEFAULT,
    kinematic_prompt: str = None,
    physics_prompt: str = None,
    rl_prompt: str = None,
    pose_prompt: str = None,
    orchestrator_prompt: str = None,
    save_output_file: bool = True,
    auto_sso_login: bool = config.AUTO_SSO_LOGIN_DEFAULT,
    clear_articles_dir: bool = config.CLEAR_ARTICLES_DIR,
    status_callback: callable = None,
    output_filename: str = config.DEFAULT_OUTPUT_FILE,
    telemetry: Optional[TelemetryManager] = None,
) -> str:
    """
    Central core execution engine for T2M Research Agent.
    Used by both CLI (main.py) and Open WebUI Pipeline (t2m_pipeline.py).
    Decoupled using TelemetryManager for clean Terminal, Langfuse v3, and SSE streaming.
    Enforces strict Fail-Fast token preservation if institutional access is required but unauthenticated.
    """
    tm = telemetry or get_telemetry()
    clean_query = extract_core_keywords(query)

    def _notify(msg: str):
        if status_callback:
            try:
                status_callback(msg)
            except Exception:
                pass

    tm.thinking(
        f"Starting T2M research pipeline for query: '{clean_query}' (Raw query: {len(query)} chars)",
        source="pipeline_runner"
    )

    if ezproxy_cookie and ezproxy_cookie.strip():
        tm.tool_result("config", "Using explicit EZproxy cookie override provided via Valves", source="auth")

    manager = EZProxyManager(cookie_override=ezproxy_cookie)

    # 🛡️ LIVE HEALTH-CHECK & AUTOMATED SSO FALLBACK:
    if enable_ieee:
        tm.tool_call("verify_live_ieee_access", args={"institution": config.IEEE_INSTITUTION_DEFAULT}, source="auth")
        _notify("🔍 Verifying IEEE institutional access...")

        is_authed, reason = manager.ensure_valid_session(
            auto_login=auto_sso_login,
            status_callback=_notify,
        )

        if not is_authed:
            tm.error(f"IEEE Authentication check failed: {reason}", source="auth")
            return build_auth_required_message(reason, query=query)

        tm.tool_result("verify_live_ieee_access", result=reason, source="auth")
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

    # 1. FETCH & RANK CANDIDATE PAPERS (CODE-FIRST)
    def fetch_candidates_for_domain(domain_key: str) -> list:
        candidate_pool_size = max(int(max_results_per_domain * 1.5), 8)
        raw_candidates = []
        seen_keys = set()
        query_terms = domains.get(domain_key, [clean_query])

        for term in query_terms:
            time.sleep(1.0)
            batch = []
            if enable_ieee:
                res = fetch_ieee_papers(term, max_results=max_results_per_domain, ezproxy_domain=ezproxy_domain)
                if res:
                    batch.extend(res)
            if enable_scholar and (len(raw_candidates) + len(batch)) < candidate_pool_size:
                res = fetch_google_scholar_papers(term, max_results=max_results_per_domain, ezproxy_domain=ezproxy_domain)
                if res:
                    batch.extend(res)
            if enable_arxiv and (len(raw_candidates) + len(batch)) < candidate_pool_size:
                res = fetch_arxiv_papers(term, max_results=max_results_per_domain)
                if res:
                    batch.extend(res)
            if enable_semantic_scholar and (len(raw_candidates) + len(batch)) < candidate_pool_size:
                res = fetch_semantic_scholar_papers(term, max_results=max_results_per_domain)
                if res:
                    batch.extend(res)

            for p in batch:
                clean_t = re.sub(r'[^a-zA-Z0-9]', '', p.get('title', '').lower())
                if clean_t and clean_t not in seen_keys:
                    seen_keys.add(clean_t)
                    raw_candidates.append(p)

            if len(raw_candidates) >= candidate_pool_size:
                break

        return rank_and_filter_candidates(
            raw_candidates,
            max_results=candidate_pool_size,
            require_code=require_code,
            prefer_code=prefer_code,
            session=manager.get_session()
        )

    _notify(f"[1/4] Fetching & ranking candidate papers (Code-First={prefer_code or require_code})...")
    tm.tool_call("fetch_papers", args=f"Domains: {list(domains.keys())}", source="fetcher")

    kinematic_candidates = fetch_candidates_for_domain("kinematic")
    physics_candidates = fetch_candidates_for_domain("physics")  
    rl_candidates = fetch_candidates_for_domain("rl")
    pose_candidates = fetch_candidates_for_domain("pose")

    logger.info(f"[*] Candidate papers fetched per domain:")
    logger.info(f"    Kinematic: {len(kinematic_candidates)} candidates")
    logger.info(f"    Physics: {len(physics_candidates)} candidates")  
    logger.info(f"    RL: {len(rl_candidates)} candidates")
    logger.info(f"    Pose: {len(pose_candidates)} candidates")

    total_candidates_pool = (
        len(kinematic_candidates) + len(physics_candidates) + len(rl_candidates) + len(pose_candidates)
    )
    tm.tool_result("fetch_papers", result=f"Fetched {total_candidates_pool} ranked candidate papers across 4 domains", source="fetcher")

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    articles_dir = os.path.join(project_root, "articles")
    
    # Optionally clear articles directory if configured
    if getattr(config, "CLEAR_ARTICLES_DIR", False):
        import shutil
        if os.path.exists(articles_dir):
            shutil.rmtree(articles_dir)
            logger.info(f"Cleared existing articles directory: {articles_dir}")
    
    os.makedirs(articles_dir, exist_ok=True)

    # 2. DOWNLOAD PDFs WITH CANDIDATE REPLENISHMENT
    _notify("[2/4] Downloading full-text PDFs with candidate replenishment...")
    tm.tool_call("download_pdfs", args=f"Target: {max_results_per_domain} per domain", source="pdf_downloader")

    secured_by_domain = {}
    unsecured_papers = []
    global_secured_keys = set()

    for domain_name, candidate_list in [
        ("kinematic", kinematic_candidates),
        ("physics", physics_candidates),
        ("rl", rl_candidates),
        ("pose", pose_candidates)
    ]:
        domain_secured = []
        for candidate in candidate_list:
            c_key = re.sub(r'[^a-zA-Z0-9]', '', candidate.get('title', '').lower())
            if len(domain_secured) < max_results_per_domain:
                if not candidate.get("fulltext_secured"):
                    download_pdfs(
                        [candidate],
                        output_dir=articles_dir,
                        session=manager.get_session(),
                        cookie_override=ezproxy_cookie
                    )
                if candidate.get("fulltext_secured"):
                    domain_secured.append(candidate)
                    global_secured_keys.add(c_key)
                else:
                    unsecured_papers.append(candidate)
            else:
                if c_key not in global_secured_keys:
                    unsecured_papers.append(candidate)

        if len(domain_secured) < max_results_per_domain:
            logger.warning(
                f"[!] Only secured {len(domain_secured)}/{max_results_per_domain} full-text papers for '{domain_name}'."
            )
        secured_by_domain[domain_name] = domain_secured

    manager.sync_session_cookies_to_disk()

    # Deduplicate secured papers across domains
    unique_secured = []
    seen_sec_keys = set()
    for d_papers in secured_by_domain.values():
        for p in d_papers:
            pkey = p.get('url') or p.get('title')
            if pkey not in seen_sec_keys:
                seen_sec_keys.add(pkey)
                unique_secured.append(p)

    logger.info(f"[*] After deduplication: {len(unique_secured)} unique secured papers")

    # Deduplicate unsecured papers
    unique_unsecured = []
    seen_unsec_keys = set(seen_sec_keys)
    for p in unsecured_papers:
        pkey = p.get('url') or p.get('title')
        if pkey not in seen_unsec_keys:
            seen_unsec_keys.add(pkey)
            unique_unsecured.append(p)

    total_candidates = len(unique_secured) + len(unique_unsecured)
    download_count = len(unique_secured)
    logger.info(f"[*] Final counts - Secured: {download_count}, Unsecured: {len(unique_unsecured)}, Total: {total_candidates}")
    tm.tool_result(
        "download_pdfs",
        result=f"Secured {download_count} full-text PDFs (Replenished from {total_candidates} candidates)",
        source="pdf_downloader"
    )

    # 2.5 DISCOVER & VERIFY GITHUB REPOSITORIES
    _notify("[2.5/4] Verifying GitHub code repositories...")
    tm.tool_call("find_github_repos", args=f"{len(unique_secured)} secured papers", source="github_finder")
    gh_count = enrich_papers_with_github(
        unique_secured,
        session=manager.get_session(),
        telemetry=tm,
        status_callback=_notify
    )
    tm.tool_result("find_github_repos", result=f"Verified GitHub repositories ({gh_count} active)", source="github_finder")
    verified_gh_urls = {
        p.get("github_url")
        for p in (unique_secured + unique_unsecured)
        if p.get("github_url") and p.get("github_url") != "N/A"
    }

    # 3. SUB-AGENTS ANALYSIS (Full-Text Secured Only)
    _notify("[3/4] Engaging AI Expert Sub-Agents on Full-Text Secured Papers...")
    tm.thinking("Engaging AI Expert Sub-Agents across 4 domains (Full-Text Secured Only)", source="orchestrator")

    kinematic_result = sanitize_markdown_table_github_urls(
        analyze_kinematic(secured_by_domain["kinematic"], custom_prompt=kinematic_prompt, telemetry=tm),
        verified_gh_urls
    )
    physics_result = sanitize_markdown_table_github_urls(
        analyze_physics_diffusion(secured_by_domain["physics"], custom_prompt=physics_prompt, telemetry=tm),
        verified_gh_urls
    )
    rl_result = sanitize_markdown_table_github_urls(
        analyze_rl_control(secured_by_domain["rl"], custom_prompt=rl_prompt, telemetry=tm),
        verified_gh_urls
    )
    pose_result = sanitize_markdown_table_github_urls(
        analyze_pose_vision(secured_by_domain["pose"], custom_prompt=pose_prompt, telemetry=tm),
        verified_gh_urls
    )

    # 4. MASTER ORCHESTRATOR SYNTHESIS
    _notify("[4/4] Engaging Master Orchestrator for literature synthesis...")
    tm.thinking("Synthesizing master literature review chapter", source="orchestrator")
    final_review = sanitize_markdown_table_github_urls(
        synthesize_literature_review(
            kinematic_result,
            physics_result,
            rl_result,
            pose_result,
            custom_prompt=orchestrator_prompt,
            telemetry=tm
        ),
        verified_gh_urls
    )

    appendix_section = build_unsecured_appendix(unique_unsecured)

    # Build response for Open WebUI & File Saving
    summary_header = (
        f"# 🎓 T2M Academic Research Report\n\n"
        f"**Query:** `{query[:100]}...` | **Extracted Search Terms:** `{clean_query}`\n"
        f"**Unique Papers Processed:** {total_candidates} | **Full-Text RAG Verified:** {len(unique_secured)} | **Paywalled/Skipped:** {len(unique_unsecured)}\n"
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
        f"{final_review}\n\n"
    )

    if appendix_section:
        summary_header += f"---\n\n{appendix_section}"

    # 5. ACADEMIC CREDIBILITY & PEER-REVIEW ENRICHMENT
    if unique_secured:
        _notify("📊 Enriching review with CrossRef and ArXiv peer-review verification...")
        tm.tool_call("enrich_literature_review", args=f"{len(unique_secured)} secured papers", source="enricher")
        summary_header = enrich_literature_review(summary_header, papers=unique_secured)
        tm.tool_result("enrich_literature_review", result="Citations verified", source="enricher")

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
            tm.tool_result("save_output_file", result=f"Report saved to {output_filename}", source="pipeline_runner")
        except Exception as e:
            tm.error(f"Failed to write review file {output_path}: {e}", source="pipeline_runner")

    tm.response(f"Research synthesis completed ({len(summary_header)} chars)", source="pipeline_runner")
    tm.close()
    return summary_header


if __name__ == "__main__":
    print("==================================================")
    print("🔬 Pipeline Runner Standalone Health Check")
    print("==================================================")
    # Validate table sanitizer
    test_raw = "| Paper | [Valid](https://github.com/wuyan01/UniPhys) | [Dead](https://github.com/QianChen113/RetinaDiff) |"
    test_sanitized = sanitize_markdown_table_github_urls(test_raw, {"https://github.com/wuyan01/UniPhys"})
    assert "[wuyan01/UniPhys](https://github.com/wuyan01/UniPhys)" in test_sanitized
    assert "QianChen113" not in test_sanitized
    assert "N/A" in test_sanitized
    print("[*] Table Sanitizer Validation: PASSED")

    # Validate code-first candidate ranking
    mock_candidates = [
        {"title": "Random Theoretical Analysis of Nonexistent Topic 9999", "citations": 500, "influential_citations": 50, "github_url": "N/A"},
        {"title": "Paper With Code", "citations": 100, "influential_citations": 10, "github_url": "https://github.com/GuyTevet/motion-diffusion-model"},
    ]
    ranked_prefer = rank_and_filter_candidates(list(mock_candidates), max_results=2, prefer_code=True)
    assert ranked_prefer[0]["title"] == "Paper With Code"
    ranked_require = rank_and_filter_candidates(list(mock_candidates), max_results=2, require_code=True)
    assert len(ranked_require) == 1
    assert ranked_require[0]["title"] == "Paper With Code"
    print("[*] Code-First Candidate Ranking Validation: PASSED")

    # Validate replenishment & appendix table generator
    mock_unsecured = [
        {"title": "Paywalled Motion Synthesis", "year": 2024, "venue": "CVPR", "citations": 42, "github_url": "https://github.com/test/repo"}
    ]
    app_md = build_unsecured_appendix(mock_unsecured)
    assert "Appendix: Papers Identified via Citations" in app_md
    assert "[test/repo](https://github.com/test/repo)" in app_md
    assert "Paywalled / Unavailable" in app_md
    print("[*] Appendix Table Generator Validation: PASSED")

    manager = EZProxyManager()
    status = manager.check_status()
    print(f"[*] Auth Status: {status['message']}")
    print("==================================================")
