"""
Configuration module for the Short Report Rebuttal Assistant
Loads environment variables and sets up paths
"""
import os
from pathlib import Path

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, use environment variables directly
    pass

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# Default to llama3.1:8b if available, fallback to llama3.1
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

# Storage paths
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", BASE_DIR / "storage" / "chroma"))
INTERNAL_DATA_DIR = Path(os.getenv("INTERNAL_DATA_DIR", BASE_DIR / "company" / "EDU"))
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", BASE_DIR / "storage" / "reports"))

# Ensure directories exist
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
INTERNAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Processing configuration
MAX_PAGES = 3  # Only process first 3 pages
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
DEFAULT_TOP_K = 6
MAX_CLAIMS = 30
MIN_CLAIMS = 8

# LLM configuration
TEMPERATURE = 0.3  # Lower temperature for more deterministic output

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
