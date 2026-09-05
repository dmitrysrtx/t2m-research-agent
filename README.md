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
   - Downloaded full-text PDF articles are stored cleanly in `articles/*.pdf`.

3. **Enhanced Paper Metadata & Comparative Tables:**
   Every processed paper extracts and synthesizes 3 crucial metadata dimensions:
   - **Citations:** Real-time citation count from academic APIs.
   - **Impact Factor / Venue Rank:** Venue classification (e.g. `CVPR (Top-tier IEEE/CVF)`, `Q1 / High Impact`).
   - **Code Repository (GitHub):** Open-source code repository URL (or `N/A` if not published).

4. **Multi-Agent RAG Pipeline:**
   - **AI Sub-Agents:** *Kinematic Models, Physics & Diffusion, RL Character Control, 3D Pose Vision*.
   - **Master Orchestrator:** Synthesizes sub-agent reports into an academic Literature Review chapter with comparative tables and research gaps.

5. **Open WebUI Pipelines & Valves Integration (`openwebui/`):**
   - Configurable Valves for enabling/disabling fetchers (`ENABLE_IEEE`, `ENABLE_SCHOLAR`, `ENABLE_ARXIV`, `ENABLE_SEMANTIC_SCHOLAR`), adjusting paper counts, and customizing system prompts.

---

## 📁 Repository Structure

```text
t2m-research-agent/
├── src/                          # CORE PYTHON SYSTEM
│   ├── auth/                     # INSTITUTIONAL AUTHENTICATION & EZPROXY
│   │   ├── __init__.py           # Package exports
│   │   ├── ezproxy_session.py    # Unified EZProxyManager & Session Engine
│   │   ├── afeka_sso.py          # Browser-driven Playwright 2FA SSO Automation
│   │   ├── ezproxy_auth.py       # URL Rewriter & Live Access Verifier
│   │   ├── import_cookies.py     # Interactive CLI Cookie Importer
│   │   ├── playwright_login.py   # Automated login compatibility wrapper
│   │   └── sso_login.py          # Direct SSO Authentication Runner
│   ├── fetchers/                 # ACADEMIC SEARCH ENGINES
│   │   ├── scholar_fetcher.py    # Google Scholar Index Fetcher
│   │   ├── ieee_fetcher.py       # IEEE Xplore & OpenAlex Metadata Search
│   │   ├── arxiv_fetcher.py      # ArXiv Preprint Fetcher
│   │   ├── semantic_scholar_fetcher.py # Semantic Scholar API
│   │   └── citation_enricher.py  # CrossRef & ArXiv Academic Credibility Enricher
│   ├── agents/                   # LLM SYNTHESIS AGENTS
│   │   ├── orchestrator.py       # Master Orchestrator LLM Agent
│   │   └── sub_agents.py         # Specialized Domain Sub-Agents
│   ├── utils/                    # CROSS-CUTTING UTILITIES
│   │   ├── pdf_downloader.py     # PDF Downloader with Authenticated Sessions
│   │   └── logger.py             # System Logger
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
- `DEFAULT_SEARCH_QUERY`: Default prompt fallback.
- `DEFAULT_OUTPUT_FILE`: Master report path (defaults to `LITERATURE_REVIEW.md`).
- `IEEE_INSTITUTION`, `IEEE_USERNAME`, `IEEE_PASSWORD`: Institutional credentials for automated 2FA login.
- `EZPROXY_DOMAIN`, `AUTO_SSO_LOGIN`: EZproxy host and auto-login flag.

---

## 🔐 Authentication & Session Management (`src/auth/`)

The framework consolidates institutional authentication and token preservation into a unified `src/auth/` package:

1. **Preemptive Live Probe (`EZProxyManager`):**
   Before querying academic search APIs or calling AI sub-agents, `EZProxyManager` executes a lightweight 1-second live probe to IEEE Xplore to verify full-text download entitlement.
2. **In-Process Automated 2FA SSO:**
   If institutional cookies are missing or expired:
   - Type `/login` in OpenWebUI (or submit a research query with `AUTO_SSO_LOGIN=True`).
   - The browser flow navigates to IEEE Xplore via Afeka College SSO and sends a 2FA push notification to your phone.
   - Simply approve with your fingerprint. The manager captures new session cookies and resumes execution.
3. **Fail-Fast Token Preservation:**
   If access is unauthenticated or push is not approved, execution halts immediately (**0 LLM tokens spent**) and returns clear resolution steps.
4. **Standalone CLI Diagnostics:**
   Every authentication module includes an isolated test block for terminal verification:
   ```bash
   # Check session status and verify live IEEE Xplore access
   python3 -m src.auth.ezproxy_session

   # Run direct IEEE live probe
   python3 -m src.auth.ezproxy_auth

   # Trigger automated 2FA login directly
   python3 -m src.auth.afeka_sso
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
