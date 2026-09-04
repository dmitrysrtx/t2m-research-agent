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
├── main.py                     # CLI entry point (runs pipeline runner + enrich_review)
├── config.py                   # Environment configuration (LLM models, API keys, limits)
├── enrich_review.py            # Enriches LITERATURE_REVIEW.md with CrossRef/ArXiv metadata table
├── Makefile                    # Automation targets (setup, run, enrich, clean)
├── README.md                   # Public repository documentation
├── Gemini.md                   # Agent system guidelines & project map (this file)
├── ezproxy_cookies.json        # Stored session cookies for institutional EZproxy access
├── LITERATURE_REVIEW.md        # Master generated literature review report (Project Root)
├── articles/                   # Target directory reserved EXCLUSIVELY for downloaded PDF papers
├── openwebui/
│   ├── t2m_pipeline.py         # Open WebUI Pipeline runner interface
│   └── t2m_openwebui_tool.py   # Open WebUI standalone search tool
└── src/
    ├── agents/
    │   ├── orchestrator.py     # Master Orchestrator prompt & synthesis logic
    │   └── sub_agents.py       # Domain expert sub-agents (Kinematic, Physics, RL, Pose)
    ├── core/
    │   └── pipeline_runner.py  # Central pipeline execution engine
    ├── fetchers/
    │   ├── arxiv_fetcher.py            # ArXiv API search fetcher
    │   ├── ieee_fetcher.py             # IEEE Xplore (OpenAlex / CrossRef / IEEE API) fetcher
    │   ├── scholar_fetcher.py          # Google Scholar (via OpenAlex) fetcher
    │   └── semantic_scholar_fetcher.py # Semantic Scholar API fetcher
    └── utils/
        ├── ezproxy_auth.py      # EZproxy URL conversion & cookie session handling
        ├── import_cookies.py    # Utility to import browser cookies
        ├── logger.py            # Logging utility
        ├── pdf_downloader.py    # PDF downloader engine using authenticated sessions
        └── playwright_login.py  # Automated login handler for EZproxy SSO
```

## Key Workflows & Execution Modes

### 1. Command Line Interface (CLI)
- Command: `python main.py` or `make run`
- Flow:
  1. `main.py` executes `execute_t2m_research()` from `src/core/pipeline_runner.py`.
  2. `pipeline_runner.py` queries active search sources, downloads full-text PDFs to `<project_root>/articles/`, runs 4 sub-agent domain analyses, synthesizes findings via Master Orchestrator, and saves the output report directly to `<project_root>/LITERATURE_REVIEW.md`.
  3. `main.py` invokes `enrich_review.py` to append the `# ACADEMIC CREDIBILITY & PEER-REVIEW VERIFICATION` table to `<project_root>/LITERATURE_REVIEW.md`.

### 2. Open WebUI Integration
- Pipeline script: `openwebui/t2m_pipeline.py`
- Tool script: `openwebui/t2m_openwebui_tool.py`
- Open WebUI calls `execute_t2m_research()`, which performs identical paper retrieval, PDF downloading to `articles/`, and review saving to `LITERATURE_REVIEW.md`.

## Output Artifact Rules
1. **`LITERATURE_REVIEW.md`**: Saved ONLY at the root of the project workspace (`<project_root>/LITERATURE_REVIEW.md`). Pipeline execution overwrites this file with fresh results rather than appending duplicate headers.
2. **`articles/` Directory**: Reserved strictly for binary full-text `.pdf` files (e.g., `articles/Paper_Title.pdf`). Do NOT duplicate timestamped `.md` files or literature reviews inside `articles/`.
