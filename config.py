import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# LLM Configuration
HF_TOKEN = os.getenv("HF_TOKEN")
DEFAULT_MODEL = "Qwen/Qwen3-4B-Instruct-2507:nscale"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)