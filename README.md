# Text-to-Motion Academic Research Agent & Multi-Agent Framework

An automated multi-agent research framework designed to discover, summarize, and synthesize academic papers on **Text-to-Motion generation, Physics-based animation, and Reinforcement Learning**. 

Includes multi-fetcher academic search across **Google Scholar**, **IEEE Xplore** (with Afeka EZproxy institutional authentication), **ArXiv**, and **Semantic Scholar**.

---

## 🌟 Key Features

1. **Multi-Source Academic Fetchers:**
   - **Google Scholar:** Direct title and abstract indexing via SerpAPI / OpenAlex fallback.
   - **IEEE Xplore + Institutional EZproxy Support:** Priority metadata retrieval via OpenAlex and IEEE Xplore REST API.
   - **ArXiv:** Pre-print paper discovery.
   - **Semantic Scholar:** Deep academic paper and citation graph indexing.

2. **Automated Output Management:**
   - Whether triggered via CLI (`main.py`) or OpenWebUI Pipeline (`t2m_pipeline.py`), the generated synthesis report is saved to:
     - `LITERATURE_REVIEW.md` (root directory)
   - **Cascading Multi-Tier PDF Ingestion:** Resolves full-text PDFs through 4 fallback tiers (Direct OA -> ArXiv conversion -> Unpaywall via DOI -> IEEE EZProxy stamp).
   - Downloaded full-text PDF articles are stored cleanly in `articles/*.pdf`.

3. **Multi-Tier GitHub Code Repository Discovery & Verification Engine:**
   Automatically resolves, verifies, and sanitizes open-source code repositories across all processed papers:
   - **Parallel Execution (`ThreadPoolExecutor max_workers=8`):** Scans candidate papers concurrently with 2.0-3.0s timeouts, slashing repository discovery time to < 1.5 seconds.
   - **Tier 1 (Direct Text Regex):** Extracts `github.com/owner/repo` from abstract text and ArXiv `<arxiv:comment>` fields.
   - **Tier 2 (Author Project Pages):** Resolves project sites (`*.github.io`) linked from abstract or comments to find repository links.
   - **Tier 3 (ArXiv Resolution & Title Discovery):** Inspects ArXiv landing pages via `arxiv_id` or queries ArXiv API by paper title to resolve comments and project pages (e.g., UniPhys).
   - **Tier 4 (Targeted Verified GitHub Search):** Searches GitHub API using clean title keywords with strict keyword overlap validation and 200 OK HTTP liveness checks (e.g., STRAPS BMVC 2020).
   - **Uniform Markdown Link Formatting:** Enforces `[owner/repo](https://github.com/owner/repo)` format across all sub-agent and orchestrator tables via `clean_github_markdown_link()`.
   - **Zero-Tolerance Dead Link Sanitization:** Masks unverified/dead links (404) from LLM prompts and strictly sanitizes Sub-Agent and Orchestrator Markdown tables to ensure dead links never appear in reports.

4. **Multi-Agent RAG Pipeline:**
   - **AI Sub-Agents:** *Kinematic Models, Physics & Diffusion, RL Character Control, 3D Pose Vision*.
   - **Master Orchestrator:** Synthesizes sub-agent reports into an academic Literature Review chapter with comparative tables and research gaps.

5. **Open WebUI Pipelines & Valves Integration (`openwebui/`):**
   - Configurable Valves for enabling/disabling fetchers (`ENABLE_IEEE`, `ENABLE_SCHOLAR`, `ENABLE_ARXIV`, `ENABLE_SEMANTIC_SCHOLAR`), code-first paper selection (`REQUIRE_CODE`, `PREFER_CODE`), adjusting paper counts, and customizing system prompts.

---

## 📁 Repository Structure

```text
t2m-research-agent/
├── academic_ranking_engine/      # HYBRID SCHOLARLY DISCOVERY & RANKING ENGINE
│   ├── __init__.py               # Package exports & public API
│   ├── models.py                 # Pydantic v2 Author & PaperMetadata schemas
│   ├── venue_classifier.py       # Venue Prestige Tiering (Tiers 1-4)
│   ├── scorer.py                 # Non-linear SOTA & Foundational scoring formulas
│   ├── client.py                 # Async Semantic Scholar & ArXiv client with backoff
│   ├── discovery_engine.py       # Dual-Bucket Blending & Sub-query Expansion
│   └── demo.py                   # Rich CLI demo runner with interactive tables
├── src/                          # CORE PYTHON SYSTEM
│   ├── auth/                     # INSTITUTIONAL AUTHENTICATION & EZPROXY
│   │   ├── __init__.py           # Package exports
│   │   ├── ezproxy_session.py    # Unified EZProxyManager & Session Engine
│   │   ├── afeka_sso.py          # Browser-driven Playwright 2FA SSO Automation
│   │   ├── ezproxy_auth.py       # URL Rewriter & Live Access Verifier
│   │   ├── import_cookies.py     # Interactive CLI Cookie Importer
│   │   ├── playwright_login.py   # Automated login compatibility wrapper
│   │   └── sso_login.py          # Direct SSO Authentication Runner
│   ├── fetchers/                 # ACADEMIC SEARCH ENGINES & ENRICHMENT
│   │   ├── scholar_fetcher.py    # Google Scholar Index Fetcher
│   │   ├── ieee_fetcher.py       # IEEE Xplore & OpenAlex Metadata Search
│   │   ├── arxiv_fetcher.py      # ArXiv Preprint Fetcher
│   │   ├── semantic_scholar_fetcher.py # Semantic Scholar API
│   │   ├── github_verifier.py    # URL Normalization & HTTP Streaming Liveness Prober
│   │   ├── github_finder.py      # Multi-Tier GitHub Code Repository Discovery Engine
│   │   └── citation_enricher.py  # CrossRef & ArXiv Academic Credibility Enricher
│   ├── agents/                   # LLM SYNTHESIS AGENTS
│   │   ├── orchestrator.py       # Master Orchestrator LLM Agent
│   │   └── sub_agents.py         # Specialized Domain Sub-Agents
│   ├── telemetry/                # DECOUPLED TELEMETRY & EVENT DISPATCHER
│   │   ├── __init__.py           # Facade & get_telemetry() factory
│   │   ├── events.py             # EventType enum & TelemetryEvent dataclass
│   │   ├── manager.py            # Central TelemetryManager (Event Dispatcher)
│   │   └── handlers/             # Modular sinks (Terminal, Langfuse v3, SSE)
│   │       ├── base.py           # BaseHandler interface
│   │       ├── terminal.py       # Rich 1-line progress CLI handler
│   │       ├── langfuse_sink.py  # Langfuse v3 background sink (silent stdout)
│   │       └── sse.py            # Server-Sent Events queue & stream generator
│   ├── utils/                    # CROSS-CUTTING UTILITIES
│   │   ├── pdf_downloader.py     # Cascading Multi-Tier PDF Ingestion Engine
│   │   ├── text_formatters.py    # Markdown GitHub Link Standardizer & Sanitizer
│   │   └── logger.py             # System Logger (file-only)
│   └── core/
│       └── pipeline_runner.py    # Central pipeline execution engine
├── openwebui/                    # OPEN WEBUI INTEGRATION LAYER
│   ├── t2m_pipeline.py           # Open WebUI Custom Pipeline Wrapper with Valves
│   └── t2m_openwebui_tool.py     # Open WebUI Importable Tool
├── LITERATURE_REVIEW.md          # Generated Literature Review & Peer-Review Table
├── articles/                     # Downloaded Full-Text PDFs
├── main.py                       # CLI Execution Entry Point
├── requirements.txt              # Dependency Specifications
└── README.md                     # Documentation
```

---

## ⚙️ Setup & Installation

### 1. Environment Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment (`.env` & `agent_config.py`)
Copy the template and edit your credentials in `.env`:
```bash
cp .env.example .env
```

`agent_config.py` (aliased to `config.py` for backward compatibility) acts as the **Single Source of Truth (SSOT)** for all system parameters, academic fetcher defaults, and LLM configuration (avoiding namespace shadowing inside Docker containers):
- `OPENROUTER_API_KEY`: API Key for LLM inference (OpenRouter / OpenAI / local vLLM).
- `API_BASE_URL`: Endpoint URL (defaults to `https://openrouter.ai/api/v1`).
- `MODEL_NAME`: Target model (defaults to `anthropic/claude-3.5-sonnet`).
- `MAX_RESULTS_PER_DOMAIN`: Search limit per domain (defaults to `5`).
- `ENABLE_IEEE`, `ENABLE_SCHOLAR`, `ENABLE_ARXIV`, `ENABLE_SEMANTIC_SCHOLAR`: Boolean fetcher toggles.
- `REQUIRE_CODE`: Strictly require verified open-source GitHub code repositories for all selected papers (defaults to `False`).
- `PREFER_CODE`: Prefer and prioritize papers with verified open-source GitHub code repositories (defaults to `True`).
- `CODE_SCORE_BOOST`: Ranking score boost awarded to papers with verified code (defaults to `35.0`).
- `SEMANTIC_SCHOLAR_FIELDS_OF_STUDY`: Restrict Semantic Scholar queries to specific domains (defaults to `"Computer Science,Engineering"`).
- `SEMANTIC_SCHOLAR_API_KEY`: Optional API Key for Semantic Scholar high rate limits.
- `SEMANTIC_SCHOLAR_MIN_CITATIONS`: Minimum citations threshold for Semantic Scholar (defaults to `0`).
- `DEFAULT_SEARCH_QUERY`: Default prompt fallback.
- `DEFAULT_OUTPUT_FILE`: Master report path (defaults to `LITERATURE_REVIEW.md`).
- `IEEE_INSTITUTION`, `IEEE_USERNAME`, `IEEE_PASSWORD`: Institutional credentials for automated 2FA login.
- `EZPROXY_DOMAIN`, `AUTO_SSO_LOGIN`: EZproxy host and auto-login flag.
- `LANGFUSE_HOST`: Langfuse v3 self-hosted instance endpoint (defaults to `http://192.168.68.53:3005`).
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`: Telemetry project credentials.
- `ENABLE_CLI_LOGS`: Toggle clean terminal progress output (`True` / `False`).

---

## 🔐 Authentication & Session Management (`src/auth/`)

The framework consolidates institutional authentication and token preservation into a unified `src/auth/` package:

1. **Preemptive Live Probe & Auto-Sync (`EZProxyManager`):**
   Before querying academic search APIs or calling AI sub-agents, `EZProxyManager` executes a live probe to IEEE Xplore to verify full-text download entitlement. Refreshed session tokens (`WLSESSION`, `seqId`, `xpluserinfo`) are automatically synchronized to `ezproxy_cookies.json` after probes and PDF downloads, keeping the session alive indefinitely.
2. **Early Active Detection & 2FA Minimization (`sso_login.py`):**
   The browser automation pre-populates existing session cookies and immediately checks if IEEE Xplore already has an active institutional session. If active, it silently refreshes credentials and resumes in seconds **without prompting 2FA**. Mobile push 2FA is requested strictly when single sign-on re-authentication is genuinely required.
3. **Strict Cookie Sanitization & Isolation:**
   Filters out 30-second ephemeral tokens (`TSaf*`), AWS removal tags (`AWSALBAPP*=_remove_`), and third-party trackers (`_cl*`, `tt*`, `_ga*`) to prevent WAF rejection and header bloat. Valve inputs never overwrite or corrupt the managed session file.
4. **Fail-Fast Token Preservation:**
   If access is unauthenticated or push is not approved, execution halts immediately (**0 LLM tokens spent**) and returns clear resolution steps.
5. **Standalone CLI Diagnostics:**
   Every authentication module includes an isolated test block for terminal verification:
   ```bash
   # Check session status and verify live IEEE Xplore access
   python3 -m src.auth.ezproxy_session

   # Run direct IEEE live probe
   python3 -m src.auth.ezproxy_auth

   # Trigger IEEE -> Afeka institutional login directly
   python3 -m src.auth.sso_login
   ```

---

## 📡 Decoupled Telemetry & Observability (`src/telemetry/`)

The framework implements the **Event Dispatcher Pattern** via `TelemetryManager`, cleanly decoupling core agent execution from logging and output sinks:

1. **Unified Event Protocol (`src/telemetry/events.py`):**
   Standardized events (`THINKING`, `TOOL_CALL`, `TOOL_RESULT`, `ERROR`, `RESPONSE`) carrying source metadata, timings, and structured payloads.
2. **Terminal Progress Sink (`TerminalHandler`):**
   Utilizes `rich` to print clean, informative 1-line progress updates. Eliminates raw JSON dumps, ANSI clobbering, and duplicate trace spam.
3. **Langfuse v3 Asynchronous Sink (`LangfuseHandler`):**
   Connects to your self-hosted Langfuse v3 dashboard (`http://192.168.68.53:3005`) via background queue. Runs completely silently (**zero stdout pollution**) and gracefully degrades if credentials are unconfigured or the server is offline.
4. **Server-Sent Events Sink (`SSEHandler`):**
   Thread-safe queue converting agent telemetry into standard SSE streams (`data: {"type": "...", "content": "..."}\n\n`) with `data: [DONE]\n\n` termination for OpenWebUI and FastAPI integration.
5. **Standalone Diagnostics:**
   ```bash
   python3 -m src.telemetry.manager
   python3 -m src.telemetry.handlers.terminal
   python3 -m src.telemetry.handlers.sse
   python3 -m src.telemetry.handlers.langfuse_sink
   ```

---

## 🔬 Academic Credibility & GitHub Verification (`src/fetchers/`)

The framework automatically verifies peer-review integrity and code availability:

1. **Direct DOI CrossRef Resolution (`src/fetchers/citation_enricher.py`):**
   - Resolves exact conference and journal venues (e.g., CVPR, ICCV, IEEE Transactions) directly via CrossRef API (`api.crossref.org/works/{doi}`).
   - Implements strict token matching (`>= 75%` overlap and length ratio verification) to prevent fuzzy title mismatches.
   - Eliminates generic placeholders (never outputs `"Peer-Reviewed Journal"`); marks unrefereed papers accurately as `"arXiv"` preprints.
2. **Verified GitHub Code Discovery (`src/fetchers/github_finder.py`):**
   - Discovers official code repositories directly from primary sources: paper abstracts, ArXiv comments, author project pages (`*.github.io`), and ArXiv landing HTML without relying on third-party aggregators.
   - Verifies HTTP liveness via streaming GET with browser `User-Agent`, distinguishing between `200 OK` (verified live), `404 Not Found` (dead link/non-existent), and `403/429` (rate-limited by GitHub - preserved as valid candidate with warning).
   - Cleans and canonicalizes URLs (strips query parameters, branch subpaths, and `.git` extensions).
3. **Standalone Diagnostics:**
   ```bash
   python3 -m src.fetchers.citation_enricher
   python3 -m src.fetchers.github_finder
   ```

---

## 🔬 Academic Paper Discovery & Hybrid Ranking Engine (`academic_ranking_engine`)

A standalone, production-ready module designed to eliminate citation-lag bias and cross-domain pollution when querying scholarly APIs.

### Key Capabilities
1. **Dual-Bucket Retrieval Architecture:**
   - **Stream A (Foundational Baselines, ~35%):** Prioritizes seminal, historical high-impact publications ($\Delta t > 2.0\text{ yrs}$) using logarithmic citation weighting and venue prestige.
   - **Stream B (Frontier / SOTA, ~65%):** Surfaces recent breakthrough papers ($\Delta t \le 2.0\text{ yrs}$) using citation velocity ($V_{cit} = C_{cit} / \Delta t$), verified code availability ($B_{code} = 15$), and open-access bonuses ($B_{oa} = 3$).
2. **Venue Prestige Classifier (`venue_classifier.py`):**
   - Maps venues via canonical aliases and regex:
     - **Tier 1 ($W_{venue} = 2.0\times$):** CVPR, ICCV, ECCV, NeurIPS, ICML, ICLR, SIGGRAPH, TOG, IEEE TPAMI, IJCV, RA-L, TRO, RSS, ICRA.
     - **Tier 2 ($W_{venue} = 1.35\times$):** WACV, BMVC, 3DV, IROS, PR, CVIU.
     - **Tier 3 ($W_{venue} = 1.0\times$):** Other peer-reviewed conferences & journals.
     - **Preprints ($W_{venue} = 0.85\times$):** arXiv and unreviewed preprints.
3. **Zero-Citation Preprint Rescue:**
   - Recent arXiv preprints with high citation velocity or open-source GitHub code are rescued and boosted into top positions rather than filtered out.
4. **Sub-Query Expansion & ArXiv Fallback:**
   - Decomposes complex multi-faceted queries (e.g., `"monocular 3d human pose physics diffusion"`) into targeted sub-queries (`"monocular 3d human pose physics"`, `"monocular 3d human pose diffusion"`, etc.) to circumvent full-text intersection throttling on Semantic Scholar bulk endpoints, with automated ArXiv query fallback.

### Running the Discovery Engine Demo
```bash
# Default demo query
python3 -m academic_ranking_engine.demo "monocular 3d human pose physics diffusion"

# Custom query
python3 -m academic_ranking_engine.demo "reinforcement learning humanoid physics control"
```

---

## 🚀 Running the Framework

### Option 1: Command Line Interface (CLI)
```bash
python3 main.py
```

### Option 2: Open WebUI Integration
1. Open your **Open WebUI** dashboard.
2. Select the `T2M Multi-Agent Academic Pipeline` model.
3. Configure **Valves** (⚙️ settings icon):
   - `ENABLE_IEEE` (Toggle IEEE Xplore searches)
   - `ENABLE_ARXIV` (Toggle open preprints)
   - `ENABLE_SCHOLAR` (Toggle Google Scholar indexing)
   - `AUTO_SSO_LOGIN` (Auto-trigger mobile push 2FA on phone when cookies expire)
   - `EZPROXY_COOKIE` (Optional raw cookie override)
4. Submit your research prompt to generate a complete multi-agent literature review!

---

## 📊 Outputs & Artifacts
- `LITERATURE_REVIEW.md`: Complete literature review report saved in root directory.
- `articles/*.pdf`: Directory containing downloaded full-text PDF files.
