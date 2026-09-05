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
    ├── fetchers/               # Layer 2: Metadata Fetchers & Citation Enrichment
    │   ├── arxiv_fetcher.py            # ArXiv API search fetcher
    │   ├── ieee_fetcher.py             # IEEE Xplore (OpenAlex / CrossRef / IEEE API) fetcher
    │   ├── scholar_fetcher.py          # Google Scholar (via OpenAlex) fetcher
    │   ├── semantic_scholar_fetcher.py # Semantic Scholar API fetcher
    │   └── citation_enricher.py        # CrossRef & ArXiv Academic Credibility Enricher
    ├── agents/                 # Layer 3: Domain Agents & Synthesis
    │   ├── orchestrator.py     # Master Orchestrator prompt & synthesis logic
    │   └── sub_agents.py       # Domain expert sub-agents (Kinematic, Physics, RL, Pose)
    ├── core/                   # Layer 4: Pipeline Execution Engine
    │   └── pipeline_runner.py  # High-level pipeline coordinator & review assembler
    └── utils/                  # Layer 5: Cross-Cutting Utilities
        ├── logger.py           # Logging utility
        └── pdf_downloader.py   # PDF downloader engine using authenticated sessions
```

## Architectural Decision Log

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
  7. Enforced standalone testability via `if __name__ == '__main__':` on all auth, fetcher, and core modules.

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
