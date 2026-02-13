"""
config/settings.py
Configurazione centralizzata sistema
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
KB_DIR = DATA_DIR / "knowledge_base"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
UPLOADS_DIR = DATA_DIR / "uploads"
EXPORTS_DIR = DATA_DIR / "exports"
LOGS_DIR = BASE_DIR / "logs"

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Embedding Model (locale, no API)
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# RAG Settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 5

# LLM Settings
DEFAULT_LLM = "groq"  # "groq" o "openai"
GROQ_MODEL = "llama-3.1-70b-versatile"
OPENAI_MODEL = "gpt-4-turbo-preview"
TEMPERATURE = 0.1
MAX_TOKENS = 2000

# App Settings
APP_TITLE = "EdilMind Enterprise"
APP_ICON = "🏗️"