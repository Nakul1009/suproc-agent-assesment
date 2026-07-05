import os
from pathlib import Path

# Project Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# LLM Configuration (Local Ollama)
# Ollama hosts an OpenAI-compatible endpoint on port 11434 by default
OLLAMA_BASE_URL = "http://localhost:11434/v1"



DEFAULT_MODEL = "qwen3:4b"