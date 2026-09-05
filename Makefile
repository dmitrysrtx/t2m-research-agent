.PHONY: all setup run enrich clean

# Default python
PYTHON = python3
VENV_DIR = venv
VENV_BIN = $(VENV_DIR)/bin

all: setup run enrich

# Create environment and install dependencies
setup:
	@echo "[*] Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "[*] Installing dependencies..."
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "[!] Copied .env.example to .env. Please configure your credentials before running."; \
	fi

# Run the research agent (fetches and analyzes papers)
run:
	@echo "[*] Running the Multi-Agent Research Framework..."
	$(VENV_BIN)/python main.py

# Enrich the generated literature review with CrossRef/ArXiv metadata
enrich:
	@echo "[*] Enriching Literature Review with citation metadata..."
	$(VENV_BIN)/python -m src.fetchers.citation_enricher

# Clean up
clean:
	@echo "[*] Cleaning up environment..."
	rm -rf $(VENV_DIR)
	rm -rf __pycache__
	find src -type d -name "__pycache__" -exec rm -rf {} +
	@echo "[*] Clean complete."
