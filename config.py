import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# LLM Configuration (NVIDIA NIM)
NVIDIA_API_KEY = os.getenv("api")
DEFAULT_MODEL = "qwen/qwen3-next-80b-a3b-instruct"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)