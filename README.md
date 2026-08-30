# Text-to-Motion Academic Research Agent & Multi-Agent Framework

An automated multi-agent research framework designed to discover, summarize, and synthesize academic papers on **Text-to-Motion generation, Physics-based animation, and Reinforcement Learning**. 

Includes priority search for **IEEE Xplore** (with Afeka EZproxy institutional authentication), **ArXiv**, and OpenAlex verification.

---

## 🌟 Key Features

1. **IEEE Xplore + Institutional EZproxy Support:**
   - Priority metadata retrieval via OpenAlex and IEEE Xplore REST API.
   - Automatic conversion of paper URLs to institutional EZproxy URLs (`ieeexplore-ieee-org.ezproxy.afeka.ac.il`).
   - Cookie session extraction via Playwright (`ezproxy_cookies.json`).
2. **Multi-Agent RAG Pipeline:**
   - AI Sub-Agents for specialized domain analysis: *Kinematic Models, Physics & Diffusion, RL Character Control, 3D Pose Vision*.
   - **Master Orchestrator:** Synthesizes domain outputs into an academic Literature Review chapter highlighting research gaps.
3. **Academic Credibility Verification (`enrich_review.py`):**
   - CrossRef API integration for citation counts, DOIs, and peer-review venue validation.
4. **Open WebUI Integration (`openwebui/`):**
   - Ready-to-import **Open WebUI Pipeline** (`openwebui/t2m_pipeline.py`) and **Tool** (`openwebui/t2m_openwebui_tool.py`) for chatting with the agent directly in Open WebUI.

---

## 📁 Repository Structure

```text
t2m-research-agent/
├── src/                          # CORE PYTHON SYSTEM
│   ├── fetchers/                 
│   │   ├── ieee_fetcher.py       # IEEE Xplore & OpenAlex Metadata Search
│   │   ├── arxiv_fetcher.py      # ArXiv Preprint Fetcher
│   │   └── semantic_scholar_fetcher.py
│   ├── agents/                   
│   │   ├── orchestrator.py       # Master Orchestrator LLM Agent
│   │   └── sub_agents.py         # Specialized Domain Sub-Agents
│   └── utils/                    
│       ├── ezproxy_auth.py       # Institutional URL Rewriter & Cookie Session Manager
│       ├── playwright_login.py   # Automated Session Login Helper
│       ├── pdf_downloader.py     # PDF Downloader with EZproxy & ArXiv Fallback
│       └── logger.py             # System Logger
├── openwebui/                    # OPEN WEBUI INTEGRATION LAYER
│   ├── t2m_pipeline.py           # Open WebUI Custom Pipeline Wrapper
│   └── t2m_openwebui_tool.py     # Open WebUI Importable Tool
├── LITERATURE_REVIEW.md          # Generated Literature Review & Peer-Review Table
├── enrich_review.py              # CrossRef Academic Credibility Enricher
├── main.py                       # CLI Execution Entry Point
├── requirements.txt              # Dependency Specifications
└── README.md                     # Documentation
```

---

## ⚙️ Setup & Installation

### 1. Environment Setup
```bash
make setup
```
Or manually:
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

## 🔐 Institutional Access (IEEE Xplore / Afeka EZproxy)

To enable seamless full-text IEEE PDF downloads:

1. **Option A (Playwright Session Helper):**
   Run the login script to authenticate via browser:
   ```bash
   python3 -m src.utils.playwright_login
   ```
   This saves an authenticated session into `ezproxy_cookies.json`.

2. **Option B (Export Cookies manually):**
   Export your browser cookies while logged into Afeka EZproxy and save them as `ezproxy_cookies.json` in the project root.

---

## 🚀 Running the Framework

### Option 1: Command Line Interface (CLI)
```bash
make run
```
or:
```bash
python3 main.py
```

### Option 2: Open WebUI Integration
1. Open your **Open WebUI** dashboard.
2. Go to **Workspace -> Tools**, click **+ Import**, and upload `openwebui/t2m_openwebui_tool.py`.
3. Or go to **Workspace -> Pipelines**, and register `openwebui/t2m_pipeline.py`.
4. Select `T2M Research Agent` from the model dropdown and start chatting!

---

## 📊 Outputs & Artifacts
- `articles/`: Directory containing secured PDF files (IEEE + ArXiv).
- `LITERATURE_REVIEW.md`: Comprehensive review with structured comparison tables and CrossRef academic verification.
