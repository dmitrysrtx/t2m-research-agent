# Text-to-Motion Research Agent

An automated multi-agent pipeline designed to discover, summarize, and synthesize academic papers on **Text-to-Motion generation, Physics-based animation, and Reinforcement Learning**.

## Features

1. **Automated Search:** Pulls the latest papers directly from the ArXiv and Semantic Scholar APIs.
2. **Quality Filtering:** Filters papers by citation count to ensure academic relevance (Semantic Scholar).
3. **Multi-Agent Synthesis:** Utilizes large language models (via OpenRouter/OpenAI API) to act as specialized sub-agents. The sub-agents extract metrics, neural architectures, dataset types, and limitations into structured Markdown tables.
4. **Master Orchestrator:** Synthesizes the sub-agents' outputs into a cohesive Academic Literature Review chapter, pinpointing the current Research Gap.
5. **PDF Downloader:** Automatically downloads the raw PDF files of the discovered papers into an `articles/` directory for direct ingestion into RAG systems (like NotebookLM).

## Prerequisites
- Python 3.10+
- Linux/Ubuntu Environment (or WSL)
- Valid API Key from OpenRouter or OpenAI

## Setup Instructions

We use a simple `Makefile` to manage the environment.

1. **Initialize the Environment:**
   Run the setup command. This will create a Python virtual environment (`venv`), install dependencies, and generate a `.env` template file.
   ```bash
   make setup
   ```

2. **Configure Environment Variables:**
   Open the generated `.env` file and insert your API key:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
   API_BASE_URL=https://openrouter.ai/api/v1
   MODEL_NAME=anthropic/claude-3.5-sonnet
   ```

3. **Run the Pipeline:**
   Execute the framework.
   ```bash
   make run
   ```
   
   *What happens next?*
   - Papers are fetched.
   - PDFs are downloaded to the `./articles/` directory (ignored by git).
   - `LITERATURE_REVIEW.md` is generated (ignored by git).

4. **Clean the Environment (Optional):**
   To delete the virtual environment and python caches, run:
   ```bash
   make clean
   ```

## Workflow Integration
After the pipeline completes, upload the generated PDF files inside the `articles/` folder to your favorite RAG architecture (e.g., Google NotebookLM, LlamaIndex) for deep in-text semantic querying.
