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
   - Configurable Valves for enabling/disabling fetchers (`ENABLE_SCHOLAR`, `ENABLE_IEEE`, `ENABLE_ARXIV`, `ENABLE_SEMANTIC_SCHOLAR`), adjusting paper counts, and customizing system prompts.

---

## 📁 Repository Structure

```text
t2m-research-agent/
├── src/                          # CORE PYTHON SYSTEM
│   ├── fetchers/                 
│   │   ├── scholar_fetcher.py    # Google Scholar Index Fetcher
│   │   ├── ieee_fetcher.py       # IEEE Xplore & OpenAlex Metadata Search
│   │   ├── arxiv_fetcher.py      # ArXiv Preprint Fetcher
│   │   └── semantic_scholar_fetcher.py # Semantic Scholar API
│   ├── agents/                   
│   │   ├── orchestrator.py       # Master Orchestrator LLM Agent
│   │   └── sub_agents.py         # Specialized Domain Sub-Agents
│   ├── utils/                    
│   │   ├── paper_utils.py        # GitHub link extractor & Impact Factor estimator
│   │   ├── ezproxy_auth.py       # Institutional URL Rewriter & Cookie Session Manager
│   │   ├── pdf_downloader.py     # PDF Downloader with EZproxy & ArXiv Fallback
│   │   └── logger.py             # System Logger
│   └── core/
│       └── pipeline_runner.py    # Core execution pipeline
├── openwebui/                    # OPEN WEBUI INTEGRATION LAYER
│   ├── t2m_pipeline.py           # Open WebUI Custom Pipeline Wrapper with Valves
│   └── t2m_openwebui_tool.py     # Open WebUI Importable Tool
├── literature_review.md          # Generated Literature Review & Peer-Review Table
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

### 2. Configure Environment (`.env`)
Edit `.env` in the root directory:
```env
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
API_BASE_URL=https://openrouter.ai/api/v1
MODEL_NAME=anthropic/claude-3.5-sonnet
EZPROXY_DOMAIN=ezproxy.afeka.ac.il
```

---

## 🚀 Running the Framework

### Option 1: Command Line Interface (CLI)
```bash
python3 main.py
```

### Option 2: Open WebUI Integration
1. Open your **Open WebUI** dashboard.
2. Go to **Admin Panel -> Pipelines**.
3. Select `t2m_pipeline (pipe)` and configure **Valves**:
   - `ENABLE_SCHOLAR` (Toggle Google Scholar)
   - `ENABLE_IEEE` (Toggle IEEE Xplore)
   - `MAX_RESULTS_PER_DOMAIN` (Set results per sub-agent domain)
4. Start a chat and receive full Markdown synthesis + automatic `LITERATURE_REVIEW.md` saved on host!

---

## 📊 Outputs & Artifacts
- `LITERATURE_REVIEW.md`: Complete literature review report saved in root directory.
- `articles/*.pdf`: Directory containing downloaded full-text PDF files.
