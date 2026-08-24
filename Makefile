.PHONY: all setup run clean

# Default python
PYTHON = python3
VENV_DIR = venv
VENV_BIN = $(VENV_DIR)/bin

all: setup run

# Create environment and install dependencies
setup:
	@echo "[*] Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "[*] Installing dependencies..."
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt
	@if [ ! -f .env ]; then \
		echo "OPENROUTER_API_KEY=your_api_key_here\nAPI_BASE_URL=https://openrouter.ai/api/v1\nMODEL_NAME=anthropic/claude-3.5-sonnet" > .env; \
		echo "[!] Created .env file. Please add your API key before running."; \
	fi

# Run the research agent
run:
	@echo "[*] Running the Multi-Agent Research Framework..."
	$(VENV_BIN)/python main.py

# Clean up
clean:
	@echo "[*] Cleaning up environment..."
	rm -rf $(VENV_DIR)
	rm -rf __pycache__
	find src -type d -name "__pycache__" -exec rm -rf {} +
	@echo "[*] Clean complete."
