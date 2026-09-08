# Gemini Project Guidelines: T2M Academic Research Agent

## Project Context & Overview
The **T2M Academic Research Agent** is a multi-agent framework for automated literature review synthesis in the domain of Text-to-Motion (T2M) human motion generation, physics-guided diffusion, reinforcement learning character control, and 3D pose estimation.

The framework fetches paper metadata from academic engines (IEEE Xplore via EZproxy, ArXiv, Google Scholar / OpenAlex, Semantic Scholar), downloads full-text PDFs into `articles/`, analyzes paper sets across domain-expert sub-agents, synthesizes a master literature review chapter into `LITERATURE_REVIEW.md`, and enriches it with peer-review citation metadata via CrossRef/ArXiv.

## Core Language & Communication Rule
- **Project Codebase & Documentation**: ALL code, docstrings, comments, commit messages, and markdown files within the repository MUST be written in **English**.
- **User Communication**: Chat interactions with the user MUST be in **Russian**.

## Directory & File Structure
```
t2m-research-agent/
├── main.py                     # CLI entry point (runs pipeline runner engine)
├── config.py                   # Environment configuration (LLM models, API keys, limits)
├── Makefile                    # Automation targets (setup, run, enrich, clean)
├── README.md                   # Public repository documentation
├── Gemini.md                   # Agent system guidelines & project map (this file)
├── ezproxy_cookies.json        # Stored session cookies for institutional EZproxy access
├── LITERATURE_REVIEW.md        # Master generated literature review report (Project Root)
├── articles/                   # Target directory reserved EXCLUSIVELY for downloaded PDF papers
├── openwebui/
│   ├── t2m_pipeline.py         # Open WebUI Pipeline runner interface with dynamic reload
│   └── t2m_openwebui_tool.py   # Open WebUI standalone search tool
└── src/
    ├── auth/                   # Layer 1: Institutional Authentication & Session Management
    │   ├── __init__.py         # Package exports & lazy attribute loader
    │   ├── ezproxy_session.py  # Unified EZProxyManager & Session Engine
    │   ├── afeka_sso.py        # Playwright-based browser 2FA SSO automation
    │   ├── ezproxy_auth.py     # URL conversion & live IEEE access verification
    │   ├── import_cookies.py   # Interactive CLI cookie importer helper
    │   ├── playwright_login.py # Backward-compatible browser login alias
    │   └── sso_login.py        # Standalone SSO authentication runner
    ├── fetchers/                 # Layer 2: Metadata Fetchers & Citation Enrichment
    │   ├── arxiv_fetcher.py            # ArXiv API search fetcher
    │   ├── ieee_fetcher.py             # IEEE Xplore (OpenAlex / CrossRef / IEEE API) fetcher
    │   ├── scholar_fetcher.py          # Google Scholar (via OpenAlex) fetcher
    │   ├── semantic_scholar_fetcher.py # Semantic Scholar API fetcher
    │   ├── github_verifier.py          # URL Normalization & Streaming Liveness Prober
    │   ├── github_finder.py            # Multi-Tier GitHub Code Repository Discovery Engine
    │   └── citation_enricher.py        # CrossRef & ArXiv Academic Credibility Enricher
    ├── agents/                 # Layer 3: Domain Agents & Synthesis
    │   ├── orchestrator.py     # Master Orchestrator prompt & synthesis logic
    │   └── sub_agents.py       # Domain expert sub-agents (Kinematic, Physics, RL, Pose)
    ├── core/                   # Layer 4: Pipeline Execution Engine
    │   └── pipeline_runner.py  # High-level pipeline coordinator & review assembler
    ├── telemetry/              # Layer 5: Decoupled Telemetry & Event Dispatcher
    │   ├── __init__.py         # Package exports & get_telemetry() factory
    │   ├── events.py           # EventType enum & TelemetryEvent data model
    │   ├── manager.py          # Central TelemetryManager (Event Dispatcher)
    │   └── handlers/           # Modular telemetry sinks
    │       ├── __init__.py     # Handler exports
    │       ├── base.py         # BaseHandler abstract sink interface
    │       ├── terminal.py     # TerminalHandler (rich 1-line progress, zero raw JSON)
    │       ├── langfuse_sink.py# LangfuseHandler (v3 SDK, background thread, no stdout)
    │       └── sse.py          # SSEHandler (thread-safe Queue & SSE stream generator)
    └── utils/                  # Layer 6: Cross-Cutting Utilities
        ├── logger.py           # Logging utility (file-only)
        └── pdf_downloader.py   # PDF downloader engine using authenticated sessions
```

## Architectural Decision Log

### 2026-09-08: Standardized Markdown Links, Parallelized Discovery & Cascading PDF Ingestion
- **Goal**: Standardize all GitHub links in sub-agent tables, narrative text, and verification summaries to clean `[owner/repo](https://github.com/owner/repo)` format, resolve the 12/20 PDF download drop-off via multi-tier fallback (Direct OA -> ArXiv -> Unpaywall -> IEEE EZproxy stamp), and parallelize repository discovery via `ThreadPoolExecutor(max_workers=8)` to eliminate sequential network latency.
- **Root Causes & Key Changes**:
  1. **Uniform Markdown Link Formatter (`src/utils/text_formatters.py`)**: Implemented `clean_github_markdown_link()` converting raw GitHub URLs and full-URL anchors into clean `[owner/repo](https://github.com/owner/repo)`.
  2. **Sub-Agent & Orchestrator Prompts (`sub_agents.py`, `orchestrator.py`)**: Standardized system prompts across all 4 sub-agents and orchestrator to mandate `[Title (Year)](URL)` in the first column and `[owner/repo](https://github.com/owner/repo)` or `N/A` in the code column. Updated `ANTI_LAZY_RULE`.
  3. **Table Sanitizer Pipeline Integration (`pipeline_runner.py`)**: Updated `sanitize_markdown_table_github_urls()` to pipe through `clean_github_markdown_link()`, guaranteeing all table links conform to the standard.
  4. **Multi-Tier Cascading PDF Downloader (`src/utils/pdf_downloader.py`)**: Implemented `resolve_fulltext_pdf_url()` and `get_pdf_candidate_urls()` covering Tier 1 (Direct OA), Tier 2 (ArXiv conversion), Tier 3 (Unpaywall via DOI), and Tier 4 (IEEE EZproxy stamp URL). Streamlined to 164 lines.
  5. **Parallel GitHub Resolution (`src/fetchers/github_finder.py`)**: Refactored `enrich_papers_with_github()` to use `ThreadPoolExecutor(max_workers=8)` with thread-safe telemetry and status dispatching via `threading.Lock()`. Reduced network candidate timeouts to `(2.0, 3.0)` seconds, reducing scan time from >10s to <1.5s.
  6. **Candidate Pool Integration (`pipeline_runner.py`)**: Updated `rank_and_filter_candidates()` to leverage concurrent `enrich_papers_with_github()` across the entire candidate pool.
  7. **SRP & File Length Limits**: Maintained `text_formatters.py` (70 lines), `pdf_downloader.py` (164 lines), `github_finder.py` (189 lines), `github_verifier.py` (100 lines), and `sub_agents.py` (143 lines) strictly under 200 lines with `0o666` permissions.

### 2026-09-08: Semantic Scholar Domain Filtering & Code-First Candidate Selection
- **Goal**: Eliminate domain bleeding in academic search (e.g. non-CS disciplines such as sports medicine, cellular biology, and thermodynamics), prevent unranked 1970s database records from unauthenticated Bulk Search, and enforce "Code-First" candidate selection so papers with verified GitHub repositories are prioritized and placed into the top positions.
- **Root Causes & Key Changes**:
  1. **Domain Enforcement (`semantic_scholar_fetcher.py`)**: Explicitly passed `fieldsOfStudy="Computer Science,Engineering"` to all Semantic Scholar queries.
  2. **Standard Search Authority & Adaptive Fallback**: Maintained `/graph/v1/paper/search` as the authoritative primary search endpoint with exponential backoff on 429. Demoted unranked Bulk Search to an emergency fallback and added post-sorting by `(year >= 2019, citations)` descending, guaranteeing high-impact CS papers are returned.
  3. **Metadata Enrichment**: Added `influentialCitationCount` and `publicationVenue` to `S2_FIELDS`, mapping direct citation metrics and venue names into paper records.
  4. **Code-First Candidate Pool Expansion (`pipeline_runner.py`)**: Expanded candidate retrieval per domain to `candidate_pool_size = max(max_results_per_domain * 2, 8)` across all enabled sources before truncation.
  5. **Early Code Discovery & Candidate Scoring**: Resolved GitHub repositories for candidates early and scored candidates via `score = (CODE_ARTIFACT_SCORE_BOOST if has_code else 0.0) + citations + influential_citations * 2.0`. Enforced `prefer_code` (papers with code ranked first) and `require_code` (strictly code-bearing papers).
  6. **Configuration & OpenWebUI Valves**: Added `REQUIRE_CODE`, `PREFER_CODE`, `CODE_SCORE_BOOST`, and `SEMANTIC_SCHOLAR_FIELDS_OF_STUDY` to `agent_config.py`, `.env`, `.env.example`, and exposed `REQUIRE_CODE` and `PREFER_CODE` in `openwebui/t2m_pipeline.py` Valves.
  7. **File Length & Testability**: Kept `semantic_scholar_fetcher.py` at 159 lines, `pipeline_runner.py` modular, and validated all components with standalone test suites.

### 2026-09-08: Multi-Tier GitHub Discovery, Pre-Print Resolution & Dead-Link Elimination
- **Goal**: Eliminate false 404 links (like unreleased preprints) from literature reviews, resolve missing repositories across Semantic Scholar papers, modularize URL verification under 200-line SRP limits, and enforce post-processing table sanitization.
- **Root Causes & Key Changes**:
  1. **Split Verification & Discovery (`github_verifier.py` & `github_finder.py`)**: Extracted URL cleaning, streaming HTTP liveness verification, candidate regex matching, and blacklist definitions into dedicated `src/fetchers/github_verifier.py` (~95 lines). Kept `github_finder.py` focused exclusively on multi-tier resolution (< 196 lines).
  2. **External Identifiers & ArXiv Preprints (`semantic_scholar_fetcher.py`)**: Added `externalIds` to `S2_FIELDS`. Parsed `arxiv_id`, `arxiv_url`, and `doi` into paper dictionaries, allowing papers retrieved from Semantic Scholar to be resolved against their ArXiv preprint pages and author project pages.
  3. **Multi-Tier Resolution (`github_finder.py`)**:
     - Tier 1: Abstract and comment text regex.
     - Tier 2: Author project pages (`*.github.io`) found in metadata.
     - Tier 3: ArXiv landing page and project link discovery via `arxiv_id` or fast title lookup on ArXiv API (`ti:"..."`).
     - Tier 4: Targeted GitHub Search API fallback verifying candidate repo descriptions against paper title keywords with >= 3 word overlap and 200 OK liveness checks (successfully discovers repositories like `STRAPS-3DHumanShapePose` for BMVC 2020).
  4. **Sub-Agent Abstract URL Redaction (`sub_agents.py`)**: Redacted unverified/dead repository links from abstracts before feeding text to the LLM, and updated sub-agent system prompts to strictly require that table cells match `GitHub Code Repo:`.
  5. **Post-Processing Markdown Table Sanitization (`pipeline_runner.py`)**: Added `sanitize_markdown_table_github_urls()` to scan generated sub-agent tables and orchestrator syntheses, replacing any unverified or dead repository links with `N/A`.
  6. **Keyword Extraction Safeguard (`pipeline_runner.py`)**: Added filtering of meta-prompt words (`perform`, `write`, `review`, etc.) in `extract_core_keywords()`, preventing search degradation when user requests vary slightly from canned templates.
  7. **OpenWebUI Pipeline Dynamic Reload**: Registered `github_verifier` in `openwebui/t2m_pipeline.py`'s dynamic hot-reload sequence.
  8. **Host File Permissions & SRP**: All modified files kept strictly under 200 lines with `0o666` permissions and `dmitryx:dmitryx` host ownership.

### 2026-09-08: Core GitHub Extraction & Liveness Verification Refactor (`github_finder.py`)
- **Goal**: Fix core extraction and verification pipeline directly at source without third-party fallback APIs, eliminate false negatives caused by naive `HEAD` requests or CloudFront 403/429 blocking, and handle author project pages (`*.github.io`).
- **Root Causes & Key Changes**:
  1. **Liveness Verification (`is_github_repo_live`)**: Replaced `requests.head()` with streaming `requests.get(..., stream=True)` with browser `User-Agent`. Explicitly distinguishes between `200 OK` (`VERIFIED`), `404 Not Found` (`NOT_FOUND`), and `403/429` (`RATE_LIMITED` - preserved as valid candidate rather than dropped).
  2. **Direct Primary Sources Only (`resolve_paper_github`)**: Resolves directly against:
     - Paper abstract text and ArXiv comment field.
     - Author project pages (`*.github.io`) linked from abstract/comments.
     - ArXiv landing page HTML (`https://arxiv.org/abs/...`).
     - Zero external aggregator API dependencies (e.g. no Papers with Code, no unconstrained Google searches).
  3. **Robust URL Canonicalization (`clean_github_url`)**: Strips enclosing brackets, quotes, trailing punctuation, query parameters, anchors, `.git` extensions, and branch subpaths (`/tree/main`, `/blob/...`).
  4. **Diagnostic Test Suite**: Added standalone diagnostic test covering real-world papers (MDM, MotionDiffuse, EMDM), non-existent 404 repositories, and project page resolution.
  5. **Modular Architecture**: Maintained file length at 193 lines (< 200 lines limit) with `0o666` permissions and `dmitryx:dmitryx` ownership.

### 2026-09-08: Academic Paper Discovery & Hybrid Ranking Engine (`academic_ranking_engine`)
- **Goal**: Implement a production-grade Python package (`academic_ranking_engine`) designed to fetch, filter, rank, and balance academic papers from scholarly APIs (Semantic Scholar Graph API with ArXiv fallback), solving citation-lag bias and cross-domain pollution.
- **Architectural Components & Implementation**:
  1. **Data Models (`models.py`)**: Pydantic v2 `Author` and `PaperMetadata` schemas with calculated properties for publication age ($\Delta t$), citation velocity ($V_{cit}$), and open-source availability (`has_code`).
  2. **Venue Tier Classifier (`venue_classifier.py`)**: Rule-based regex and normalized string matcher assigning venue tiers: Tier 1 ($W_{venue} = 2.0\times$), Tier 2 ($1.35\times$), Tier 3 ($1.0\times$), and Preprints ($0.85\times$).
  3. **Scoring Engine (`scorer.py`)**: Mathematically rigorous non-linear scoring applying $S_{SOTA} = W_{venue} \cdot (1.2 \cdot V_{cit} + 0.5 \cdot \text{InflCit}) + B_{code} + B_{oa} + B_{author}$ for recent works ($\Delta t \le 2.0$) and $S_{Found} = W_{venue} \cdot [0.8 \cdot \ln(1 + C_{cit}) + 0.4 \cdot \text{InflCit}] + \dots$ for historical baselines ($\Delta t > 2.0$).
  4. **Async Scholar Client (`client.py`)**: Asynchronous `httpx` client with domain locking (`Computer Science, Engineering`), unauthenticated bulk search optimization, and automated ArXiv fallback.
  5. **Dual-Bucket Discovery Engine (`discovery_engine.py`)**: Orchestrates 35% Foundational / 65% SOTA ratio blending, cross-stream deduplication via normalized titles, sub-query decomposition for multi-faceted keyword queries, and zero-citation preprint rescue.
  6. **Interactive CLI Demo (`demo.py`)**: Rich color-coded terminal dashboard displaying ranked publications, venue tiers, citation velocities, and score breakdowns.
  7. **Modular Constraints**: All module files maintained under 200 lines with standalone `if __name__ == '__main__':` test runners and `dmitryx:dmitryx` host ownership.

### 2026-09-08: Semantic Scholar Resilience, 429 Rate-Limit Mitigation & Bulk Search Fallback
- **Goal**: Resolve HTTP 429 throttling on Semantic Scholar API that caused Kinematic and Pose/Vision sub-agents to retrieve 0 papers in unauthenticated mode, add official API key authentication, implement adaptive exponential backoff with `Retry-After` header parsing, and add seamless bulk search fallback.
- **Root Causes & Key Changes**:
  1. **HTTP 429 Rate Limiting & Retry Cool-Down**: Fixed flat 5s sleep in `semantic_scholar_fetcher.py`. Introduced adaptive backoff (`[4s, 8s, 14s]`) and dynamic parsing of the `Retry-After` header returned by CloudFront/API Gateway.
  2. **Unauthenticated Strategy — Direct Bulk Search**: CloudFront aggressively throttles `/graph/v1/paper/search` for unauthenticated IPs with HTTP 429, but `/graph/v1/paper/search/bulk` offers high throughput without aggressive throttling. In unauthenticated mode, the fetcher queries Bulk Search directly, completely circumventing 429 errors.
  3. **Bulk Search `tldr` Incompatibility Fix**: Removed `tldr` from `S2_FIELDS`. Semantic Scholar's `/paper/search/bulk` endpoint strictly rejects `tldr` with `HTTP 400: {"error":"Unrecognized or unsupported fields: [tldr]"}`, which previously caused the fallback to fail silently.
  4. **OpenWebUI Pipeline Dynamic Reloading**: Added `src.fetchers.semantic_scholar_fetcher`, `scholar_fetcher`, `ieee_fetcher`, and `arxiv_fetcher` to the `importlib.reload(...)` block in `openwebui/t2m_pipeline.py`, ensuring containerized OpenWebUI instances immediately execute refreshed code without container restarts.
  5. **Official API Key Authentication (`SEMANTIC_SCHOLAR_API_KEY`)**: Centralized API key configuration in `agent_config.py`, `.env`, `.env.example`, and OpenWebUI Valves, transmitting `x-api-key` headers to grant high-throughput access.
  6. **Relaxed Citation Filtering**: Changed default `min_citations` from `2` to `0` (configurable via `SEMANTIC_SCHOLAR_MIN_CITATIONS`), preventing recent (2023–2026) high-value publications from being dropped.
  7. **Pipeline Runner Scholar Integration**: Fixed missing `enable_scholar` branch in `src/core/pipeline_runner.py`'s `fetch_papers_for_domain` loop, ensuring Google Scholar (OpenAlex/Crossref) executes when enabled.

### 2026-09-07: Resilient Institutional Authentication, Session Persistence & 2FA Elimination
- **Goal**: Eliminate repeated 2FA (mobile fingerprint/push approval) prompts on every pipeline run, prevent stale cookie shadowing, auto-synchronize live session tokens back to disk, and sanitize tracking/ephemeral tokens.
- **Root Causes & Key Changes**:
  1. **Session Cookie Re-Use & Early Active Detection (`sso_login.py`):** Pre-populated Playwright browser contexts with existing institutional cookies (`context.add_cookies()`) and added early detection for active Afeka College sessions on IEEE Xplore. If institutional access is already granted, it extracts updated cookies and exits immediately without prompting 2FA or retyping credentials.
  2. **Automated Live Cookie Sync to Disk (`ezproxy_session.py` & `pipeline_runner.py`):** Added `sync_session_cookies_to_disk()` to `EZProxyManager`. Invoked automatically during live health checks and immediately after PDF downloads in `pipeline_runner.py` to persist refreshed tokens (`WLSESSION`, `seqId`, `xpluserinfo`) back to `ezproxy_cookies.json`, preventing session expiration while idle.
  3. **Strict Cookie Sanitization (`ezproxy_auth.py`):** Filtered out ephemeral F5 ASM tokens (`TSaf*` with 30s TTL), AWS removal markers (`AWSALBAPP*=_remove_`), and third-party trackers (`_cl*`, `tt*`, `_ga*`, etc.) on both disk load and disk save.
  4. **Valve Precedence & Process Isolation Fix (`ezproxy_auth.py` & `pipeline_runner.py`):** Guaranteed `ezproxy_cookies.json` is loaded whenever it contains a valid `ERIGHTS` token. Removed global `os.environ["EZPROXY_COOKIE"]` mutation in `pipeline_runner.py` so empty/stale valve inputs no longer poison subsequent runs in the container process.
  5. **Resilient Health Probes (`ezproxy_auth.py`):** Increased live probe timeout from 8s to 15s to eliminate false-positive network timeouts, properly resolved relative redirects via `urljoin`, and merged any refreshed response cookies directly to disk.
  6. **Host File Ownership & Permissions:** Enforced standard host user ownership (`dmitryx:dmitryx`) and proper mode differentiation (`0o777` for directories, `0o666` for files).

### 2026-09-07: Publication Venue Accuracy, DOI Direct Lookup & Verified GitHub Discovery
- **Goal**: Resolve inaccurate venue names (`"Peer-Reviewed Journal"`, false-positive book chapters like `"Human Pose Analysis"`), wrong publication years (2025 instead of 2020), supplementary media artifacts (`.mp4`), and dead/irrelevant GitHub links.
- **Root Causes & Key Changes**:
  1. **Direct DOI CrossRef Lookup (`citation_enricher.py`):** Prioritized direct DOI API queries (`https://api.crossref.org/works/{doi}`) instead of fuzzy title search. Extracted conference names from `container-title`, `event.name` (e.g. CVPR, ICCV, ICRA), `publisher`, and `group-title`. Completely eliminated the hardcoded string `"Peer-Reviewed Journal"`.
  2. **Strict Title Match Safeguard:** Replaced loose 0.4 token threshold with strict `>= 0.75` token overlap and `>= 0.6` character length ratio, preventing short common keywords from matching unrelated book chapters. If CrossRef search lacks high confidence, upstream fetcher metadata is preserved.
  3. **ArXiv & Preprint Categorization:** ArXiv publications without external peer-reviewed DOIs or journal refs are explicitly marked as venue `"arXiv"` and status `"Preprint (arXiv)"`.
  4. **Supplementary Media Filtering:** Filtered non-paper media files (`.mp4`, `.avi`, `.mov`, `.supp`, `.zip`) across `ieee_fetcher.py`, `scholar_fetcher.py`, and `citation_enricher.py`.
  5. **Verified GitHub Liveness & Loose Search Removal (`github_finder.py`):** Removed unconstrained keyword GitHub search API fallback that returned unrelated repos (e.g. market reports). Added `is_github_repo_live` HTTP HEAD verification to ensure candidate repositories exist, are public, and return HTTP 200 before attaching them; otherwise cleanly outputs `N/A`.
  6. **OpenAlex Venue & Citation Enhancement (`scholar_fetcher.py`):** Updated OpenAlex parsing to extract `raw_source_name` and alternate locations when primary `source.display_name` is null, and preserved `cited_by_count`.

### 2026-09-07: Multi-Tier GitHub Code Repository Discovery Engine (`github_finder.py`)
- **Goal**: Automatically discover, extract, and canonicalize GitHub open-source code repositories for academic papers, eliminating universal `N/A` placeholders across Sub-Agent tables and Master Review synthesis.
- **Key Changes**:
  1. **Dedicated Module (`src/fetchers/github_finder.py`):** Implemented multi-tier discovery:
     - **Tier 1 (Instant Abstract/Comment Extraction):** High-precision regex extracts `github.com/{owner}/{repo}` and `{owner}.github.io/{repo}` from abstract and ArXiv `<arxiv:comment>` fields.
     - **Tier 2 (Landing Page HTML Inspection):** Scans download landing pages during PDF acquisition or URL resolution.
     - **Tier 3 (Targeted Search Fallback):** Queries GitHub REST Search API (`in:name,description`) using cleaned title keywords with rate-limit and bot-protection safeguards.
     - **Canonicalization:** Cleans trailing punctuation, strips branch subpaths (`/tree/main`, `/blob/...`, `.git`), and filters out service endpoints (`/topics`, `/features`, `/pricing`).
  2. **Fetchers Integration:** Updated `arxiv_fetcher.py` to parse `<arxiv:comment>`, `ieee_fetcher.py`, `scholar_fetcher.py`, and `semantic_scholar_fetcher.py` to run `extract_github_url` on paper abstracts.
  3. **PDF Downloader Integration (`pdf_downloader.py`):** Scans HTML responses during PDF downloading and attaches discovered repositories to paper dictionaries.
  4. **Pipeline Execution Integration (`pipeline_runner.py`):** Added Step 2.5 (`find_github_repos`) between PDF download and Sub-Agent prompts, dispatching telemetry events to OpenWebUI and Terminal.
  5. **Academic Credibility Table Enrichment (`citation_enricher.py`):** Added `Code Repository` column to the `# ACADEMIC CREDIBILITY & PEER-REVIEW VERIFICATION` table.
  6. **OpenWebUI Pipeline Dynamic Reload:** Added `src.fetchers.github_finder` to hot-reloading list in `openwebui/t2m_pipeline.py`.

### 2026-09-06: Decoupled Telemetry Architecture (Event Dispatcher, Rich Terminal, Langfuse v3, SSE)
- **Goal**: Decouple core agent execution from logging and output handlers following the Event Dispatcher Pattern, eliminate raw JSON terminal clutter, silence background tracing, and provide SSE streaming.
- **Key Changes**:
  1. **Event Dispatcher (`src/telemetry/`):** Created `TelemetryManager` and unified `TelemetryEvent` contract (`THINKING`, `TOOL_CALL`, `TOOL_RESULT`, `ERROR`, `RESPONSE`).
  2. **Rich 1-Line Progress Terminal Sink (`TerminalHandler`):** Replaced verbose multi-line stdout dumps with clean, color-coded, 1-line status updates using `rich`. Completely eliminated raw JSON and duplicate line dumps.
  3. **Langfuse v3 SDK Asynchronous Sink (`LangfuseHandler`):** Integrated background event dispatching to self-hosted Langfuse v3 (`http://192.168.68.53:3005`). Silenced `langfuse` logger (`logging.CRITICAL`, non-propagating) to guarantee zero stdout pollution. Handled missing keys and connection timeouts gracefully without blocking the agent.
  4. **Server-Sent Events Sink (`SSEHandler`):** Created thread-safe queue generating compliant SSE streams (`data: {...}\n\n`) ending with `data: [DONE]\n\n` for OpenWebUI and FastAPI integration.
  5. **Core Engine Instrumentation:** Updated `pipeline_runner.py`, `sub_agents.py`, and `orchestrator.py` to emit structured events instead of direct `print` calls.
  6. **Clean Logging:** Configured `logger.py` to write strictly to `research_agent.log`, preventing duplicate trace messages in terminal.
  7. **OpenWebUI Pipeline Integration:** Integrated `OpenWebUIAdapterSink` and `SSEHandler` into `openwebui/t2m_pipeline.py` with dynamic hot-reloading.

### 2026-09-05: IEEE Xplore / Afeka College Institutional SSO Refactor & Cookie Sanitization
- **Goal**: Resolve authentication flow failure, fix Playwright selector deadlock, eliminate synchronous form submit blocking, and prevent HTTP 400 Bad Request caused by cookie bloat.
- **Root Causes & Solutions**:
  1. **Direct WAYF OpenAthens Navigation**: Added direct navigation to `AFEKA_WAYF_URL` (`https://ieeexplore.ieee.org/servlet/wayf.jsp?entityId=https://idp.afeka.ac.il/openathens...`) with resilient fallback to modal typeahead discovery, avoiding brittle Angular UI hierarchies.
  2. **Playwright Form Submission Deadlock**: Replaced blocking `submit.click()` with `no_wait_after=True` and prompt-first notification so the user receives the 2FA push instruction immediately while the browser awaits SAML return (`page.wait_for_url("**/ieeexplore.ieee.org/**")`).
  3. **Cookie Sanitization & CloudFront 400 Fix**: Stripped 3rd-party tracking cookies (Taboola, LinkedIn, TikTok, Adobe, GA) and eliminated duplicate cookie injection on both `.ieee.org` and `ieeexplore.ieee.org`, keeping request headers lean and preventing CloudFront `HTTP 400 Bad Request`.
  4. **Headless Browser Dependencies**: Verified and installed required Linux shared libraries (`libatk-1.0`, `libcups2`, `libgbm1`, etc.) for Playwright Chromium.
  5. **Modular Code Architecture**: Maintained all modules in `src/auth/` under 200 lines with standalone `__main__` diagnostics.

### 2026-09-05: Single Source of Truth (SSOT) Configuration Consolidation
- **Goal**: Eliminate hardcoded fallbacks and duplicate configuration across modules (`main.py`, `openwebui/t2m_pipeline.py`, `src/core/pipeline_runner.py`, `src/fetchers/`), making `config.py` the authoritative Single Source of Truth.
- **Key Changes**:
  1. Centralized all runtime defaults and environment variable overrides in `config.py` (`API_KEY`, `BASE_URL`, `MODEL_NAME`, `MAX_RESULTS_PER_DOMAIN`, `ENABLE_IEEE_DEFAULT`, `ENABLE_SCHOLAR_DEFAULT`, `ENABLE_ARXIV_DEFAULT`, `ENABLE_SEMANTIC_SCHOLAR_DEFAULT`, `DEFAULT_OUTPUT_FILE`, `DEFAULT_SEARCH_QUERY`, `EZPROXY_DOMAIN_DEFAULT`, `AUTO_SSO_LOGIN_DEFAULT`, `IEEE_INSTITUTION_DEFAULT`).
  2. Refactored `openwebui/t2m_pipeline.py` `Valves` schema and fallback resolution to bind strictly to `config.*` constants, and added `config` to dynamic hot-reloading.
  3. Refactored `main.py` and `src/core/pipeline_runner.py` function signatures and caller parameters to use `config.*` defaults.
  4. Updated all fetchers (`src/fetchers/arxiv_fetcher.py`, `ieee_fetcher.py`, `scholar_fetcher.py`, `semantic_scholar_fetcher.py`) to reference unified default query and limit constants.
  5. Updated `.env.example` with full variable definitions and updated `Makefile` `setup` target to safely copy `.env.example` (`cp .env.example .env`).
  6. Added standalone test runner to `config.py` (`python3 config.py`).
  7. Documented `config.py` as the application SSOT in `README.md` and `Gemini.md`.

### 2026-09-05: Configuration Simplification & Import Cleanup
- **Goal**: Eliminate dead-code in `config.py` and replace complex dynamic importlib loading in `src/agents/sub_agents.py` with standard imports.
- **Key Changes**:
  1. Replaced unused `MAX_PAPERS_PER_CATEGORY` with `MAX_RESULTS_PER_DOMAIN = int(os.getenv("MAX_RESULTS_PER_DOMAIN", "5"))` in `config.py`.
  2. Simplified config loading in `src/agents/sub_agents.py` to direct `from config import API_KEY, BASE_URL, MODEL_NAME`.
  3. Cleaned up `main.py` to source `MAX_RESULTS_PER_DOMAIN` from `config`.

### 2026-09-05: Integrated Citation & Peer-Review Enrichment
- **Goal**: Embed academic credibility analysis directly into the pipeline lifecycle and eliminate external root scripts.
- **Key Changes**:
  1. Migrated CrossRef and ArXiv verification logic from `enrich_review.py` into `src/fetchers/citation_enricher.py`.
  2. Integrated `enrich_literature_review()` directly into `src/core/pipeline_runner.py`, enriching the report automatically before saving `LITERATURE_REVIEW.md`.
  3. Removed obsolete root file `enrich_review.py` and updated `main.py` and `Makefile`.
  4. Added standalone module testability to `citation_enricher.py` (`python3 -m src.fetchers.citation_enricher`).

### 2026-09-05: Unified `src/auth/` & Infrastructure Deprecation
- **Goal**: Consolidate scattered authentication logic into a dedicated, modular package following Single Responsibility Principle (SRP) and file length limits (<200 lines).
- **Key Changes**:
  1. Created `src/auth/` package with `EZProxyManager` in `src/auth/ezproxy_session.py` to orchestrate session creation, live health checks, and automated 2FA login.
  2. Migrated browser automation from `infra/auth_service/browser_flow.py` into `src/auth/afeka_sso.py`.
  3. Relocated `ezproxy_auth.py`, `import_cookies.py`, `playwright_login.py`, and `sso_login.py` from `src/utils/` to `src/auth/`.
  4. Fully deprecated and removed `infra/auth_service/` (standalone Flask server on port 8055) in favor of direct in-process execution.
  5. Cleaned up `src/utils/` so only cross-cutting utilities (`logger.py` and `pdf_downloader.py`) remain.
  6. Updated all dependent modules (`src/fetchers/`, `src/core/pipeline_runner.py`, `openwebui/t2m_pipeline.py`).
### 2026-09-05: IEEE PDF Download Engine & Live Auth Verification Fixes
- **Goal**: Resolve silent PDF download failures in OpenWebUI and eliminate false-positive authentication status reports.
- **Root Causes & Solutions**:
  1. **Live Auth False-Positive**: In `src/auth/ezproxy_auth.py`, `verify_live_ieee_access()` evaluated `if "pdf" in loc.lower()` before checking login indicators. When IEEE responded with `302 Found` to `login.jsp?url=%2FstampPDF%2FgetPDF.jsp...&authDecision=-203`, the query string triggered a false-positive pass. Fixed by enabling `allow_redirects=True`, strictly verifying binary `%PDF` streams on 200 responses, and checking for login walls across redirect history.
  2. **OpenAlex `NameError: re`**: Added missing `import re` in `src/fetchers/ieee_fetcher.py`.
  3. **Crossref Malformed Article Numbers**: Replaced broken `.split(".")[0]` logic with regex matching (`r'(\d{6,8})(?:/[^/]+)?$'`) and canonical DOI URL fallback (`https://doi.org/{doi}`).
  4. **PDF Downloader DOI Resolution**: Updated `src/utils/pdf_downloader.py` to follow DOI redirects to `/document/<arnumber>`, resolve to `stampPDF/getPDF.jsp`, strictly enforce binary PDF validation (`is_pdf_bytes`), and accept session / cookie overrides directly from pipeline runner.
  5. **Docker Config Shadowing**: Renamed pipeline reloader to target `agent_config.py` explicitly, avoiding collisions with OpenWebUI's internal `config.py`.

### 2026-09-05: SSO Browser Automation Phantom Status Fix & Multi-Source PDF Downloader
- **Goal**: Eliminate false status callbacks in `afeka_sso.py`, prevent dumping unauthenticated guest cookies into `ezproxy_cookies.json`, fix static header poisoning, and enable direct PDF resolution for ArXiv and open-access publications.
- **Root Causes & Solutions**:
  1. **Phantom 2FA Notification in `afeka_sso.py`**: The status callback reporting mobile push notification was triggered unconditionally even when Angular modal component `<xpl-seamless-access>` was stuck on loading spinner or blocked by third-party storage partitioning. Furthermore, `page.wait_for_url("**/ieeexplore.ieee.org/**")` immediately returned true because the browser was still on IEEE Xplore, dumping unauthenticated guest cookies. Fixed by strictly verifying navigation to `sso.afeka.ac.il`, only sending push notifications when credentials are submitted, and verifying live access with a test session before overwriting `ezproxy_cookies.json`.
  2. **Session Cookie Header Poisoning in `ezproxy_session.py`**: Removed `session.headers["Cookie"] = "; ".join(...)` which sent hardcoded IEEE cookies to foreign domains (ArXiv, CrossRef, DOI resolvers). Restricted cookies to `.ieee.org` in `session.cookies` without duplicate sub-domain binding.
  3. **Multi-Source ArXiv / OpenAccess Resolution in `pdf_downloader.py`**: Added `resolve_direct_pdf_url()` to transform ArXiv abstract URLs (`arxiv.org/abs/...`) to direct binary endpoints (`arxiv.org/pdf/...pdf`), added ArXiv link detection in landing page HTML, added `Referer` headers for IEEE requests, and decoupled requests for non-IEEE sources. Verified direct PDF downloads for ArXiv papers.
  4. **Diagnostic Transparency & Fast Probe Optimization**: In `src/auth/ezproxy_auth.py`, updated `verify_live_ieee_access()` with `allow_redirects=False` for sub-second fail-fast probe checks, and enhanced diagnostic messages to explicitly report when `ezproxy_cookies.json` was parsed successfully but lacks the institutional `ERIGHTS` token.
  5. **IEEE SAML Federated Institutional Authentication Flow (`sso_login.py`)**: Completely refactored the institutional authentication engine in `src/auth/sso_login.py`. Rather than authenticating directly against Afeka (`sso.afeka.ac.il/my.policy`) which only yielded internal IdP cookies (`MRHSession`), the automation begins at `https://ieeexplore.ieee.org`, triggers "Institutional Sign In" -> "Access Through Your Institution", searches for "Afeka College", and redirects into Afeka's SAML IdP with the IEEE authentication request. Once credentials are submitted and the user approves the 2FA push on their mobile phone, the browser completes the SAML callback to IEEE Xplore, acquiring the authentic institutional entitlement token (`ERIGHTS`). All cookies are dumped into `ezproxy_cookies.json`.
  6. **PDF Downloader Session & User-Agent Preservation**: Updated `src/utils/pdf_downloader.py` to route DOI links through `session` so that redirects to `ieeexplore.ieee.org` preserve institutional cookies and browser User-Agent headers, preventing HTTP 420 rate-limiting and paywall re-routing.

## Key Workflows & Execution Modes

### 1. Command Line Interface (CLI)
- Command: `python main.py` or `make run`
- Flow:
  1. `main.py` executes `execute_t2m_research()` from `src/core/pipeline_runner.py`.
  2. `pipeline_runner.py` verifies IEEE access via `EZProxyManager`, queries active search sources, downloads full-text PDFs to `<project_root>/articles/`, runs 4 sub-agent domain analyses, synthesizes findings via Master Orchestrator, automatically enriches the report with the `# ACADEMIC CREDIBILITY & PEER-REVIEW VERIFICATION` table via `citation_enricher.py`, and saves the final output report directly to `<project_root>/LITERATURE_REVIEW.md`.

### 2. Open WebUI Integration
- Pipeline script: `openwebui/t2m_pipeline.py`
- Tool script: `openwebui/t2m_openwebui_tool.py`
- Open WebUI calls `execute_t2m_research()`, which performs identical paper retrieval, PDF downloading to `articles/`, credibility enrichment, and review saving to `LITERATURE_REVIEW.md`. Hot-reloading dynamically reloads `src.auth`, `src.fetchers`, `src.core`, and `src.agents` modules without restarting the container.

## Output Artifact Rules
1. **`LITERATURE_REVIEW.md`**: Saved ONLY at the root of the project workspace (`<project_root>/LITERATURE_REVIEW.md`). Pipeline execution overwrites this file with fresh results rather than appending duplicate headers.
2. **`articles/` Directory**: Reserved strictly for binary full-text `.pdf` files (e.g., `articles/Paper_Title.pdf`). Do NOT duplicate timestamped `.md` files or literature reviews inside `articles/`.
