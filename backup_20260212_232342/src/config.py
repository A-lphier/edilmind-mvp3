"""
EdilMind - Configurazione centrale
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import re

load_dotenv()

# API Keys
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
UNSTRUCTURED_API_KEY = os.getenv("UNSTRUCTURED_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdf_bandi"
CACHE_DIR = DATA_DIR / "cache"

# Embedding
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIMENSION = 768

# SOA Categories
CATEGORIE_SOA = {
    "OG1": "Edifici civili e industriali",
    "OG2": "Restauro e manutenzione beni tutelati",
    "OG3": "Strade, ponti, ferrovie",
    "OG11": "Impianti tecnologici",
    "OS21": "Opere strutturali speciali",
}

CLASSI_IMPORTI_MAX = {
    "I": 258_000,
    "II": 516_000,
    "III": 1_033_000,
    "IV": 2_066_000,
    "V": 3_500_000,
    "VI": 5_165_000,
    "VII": 10_329_000,
    "VIII": float("inf"),
}

# Regex patterns
REGEX_CPV = re.compile(r"\b(\d{8}-\d)\b")
REGEX_IMPORTO = re.compile(r"(€|EUR|euro)\s*([\d.,]+)", re.IGNORECASE)
REGEX_CIG = re.compile(r"\bCIG[:\s]*([A-Z0-9]{10})\b", re.IGNORECASE)
REGEX_CATEGORIA_SOA = re.compile(r"\b(OG|OS)\s*(\d{1,2})\b", re.IGNORECASE)
REGEX_CLASSE = re.compile(r"\bClassifica[:\s]*(I{1,3}|IV|V{1,3}I{0,3})\b", re.IGNORECASE)

# Certificazioni
CERTIFICAZIONI_RILEVANTI = [
    "ISO 9001", "ISO 14001", "ISO 45001",
    "CAM", "Criteri Ambientali Minimi",
    "parità di genere", "white list"
]

# Sezioni disciplinare ANAC
SEZIONI_DISCIPLINARE = {
    "oggetto": ["OGGETTO DELL'APPALTO", "IMPORTO E SUDDIVISIONE"],
    "durata": ["DURATA"],
    "requisiti_generali": ["REQUISITI DI ORDINE GENERALE"],
    "requisiti_speciali": ["REQUISITI DI ORDINE SPECIALE", "CAPACIT"],
    "criterio_aggiudicazione": ["CRITERIO DI AGGIUDICAZIONE"],
    "revisione_prezzi": ["REVISIONE PREZZI"],
}
