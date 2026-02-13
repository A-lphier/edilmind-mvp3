"""
EdilMind - Configurazione centrale
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import re

from pathlib import Path
import os

# Trova .env nella root del progetto
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Debug (rimuovere dopo)
print(f"🔍 Cercando .env in: {env_path}")
print(f"✓ File esiste: {env_path.exists()}")
print(f"✓ SUPABASE_URL caricato: {os.getenv('SUPABASE_URL') is not None}")

# API Keys
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdf_bandi"
CACHE_DIR = DATA_DIR / "cache"
UPLOADS_DIR = DATA_DIR / "uploads"

# Crea directory se non esistono
for d in [DATA_DIR, PDF_DIR, CACHE_DIR, UPLOADS_DIR]:
    d.mkdir(exist_ok=True, parents=True)

# SOA
CATEGORIE_SOA = {
    "OG1": "Edifici civili e industriali",
    "OG2": "Restauro e manutenzione beni tutelati",
    "OG3": "Strade, ponti, ferrovie, metropolitane",
    "OG4": "Opere idrauliche",
    "OG5": "Dighe",
    "OG6": "Acquedotti, gasdotti, oleodotti",
    "OG7": "Opere marittime e lavori di dragaggio",
    "OG8": "Opere fluviali, di difesa e sistemazione idraulica",
    "OG9": "Impianti per la produzione di energia elettrica",
    "OG10": "Impianti per la trasformazione alta/media tensione",
    "OG11": "Impianti tecnologici",
    "OG12": "Opere ed impianti di bonifica e protezione ambientale",
    "OG13": "Opere di ingegneria naturalistica",
    "OS1": "Lavori in terra",
    "OS2-A": "Superfici decorate di beni immobili del patrimonio culturale",
    "OS2-B": "Beni culturali mobili di interesse storico, artistico, archeologico",
    "OS3": "Impianti idrico-sanitario, cucine, lavanderie",
    "OS4": "Impianti elettromeccanici trasportatori",
    "OS5": "Impianti pneumatici e antintrusione",
    "OS6": "Finiture di opere generali in materiali lignei, plastici, metallici",
    "OS7": "Finiture di opere generali di natura edile e tecnica",
    "OS8": "Opere di impermeabilizzazione",
    "OS9": "Impianti per la segnaletica luminosa",
    "OS10": "Segnaletica stradale non luminosa",
    "OS11": "Armamento ferroviario",
    "OS12-A": "Barriere stradali di sicurezza",
    "OS12-B": "Barriere paramassi, fermaneve e simili",
    "OS13": "Strutture prefabbricate in cemento armato",
    "OS14": "Impianti di smaltimento e recupero rifiuti",
    "OS18-A": "Componenti strutturali in acciaio",
    "OS18-B": "Componenti per facciate continue",
    "OS19": "Impianti di reti di telecomunicazione e di trasmissione dati",
    "OS20-A": "Rilevamenti topografici",
    "OS20-B": "Indagini geognostiche",
    "OS21": "Opere strutturali speciali",
    "OS22": "Impianti di potabilizzazione e depurazione",
    "OS23": "Demolizione opere",
    "OS24": "Verde e arredo urbano",
    "OS25": "Scavi archeologici",
    "OS28": "Impianti termici e di condizionamento",
    "OS29": "Armamento ferroviario alta velocità",
    "OS30": "Impianti interni elettrici, telefonici, radiotelefonici e televisivi",
    "OS32": "Strutture in legno",
    "OS33": "Coperture speciali",
    "OS34": "Sistemi antirumore per infrastrutture di mobilità",
    "OS35": "Interventi a basso impatto ambientale",
}

CLASSI_IMPORTI_MAX = {
    "I": 258_000,
    "II": 516_000,
    "III": 1_033_000,
    "III-bis": 1_500_000,
    "IV": 2_066_000,
    "IV-bis": 3_500_000,
    "V": 5_165_000,
    "VI": 10_329_000,
    "VII": 15_494_000,
    "VIII": float("inf"),
}

# Regex
REGEX_CPV = re.compile(r"\b(\d{8}-\d)\b")
REGEX_IMPORTO = re.compile(r"(€|EUR|euro)\s*([\d.,]+)", re.IGNORECASE)
REGEX_CIG = re.compile(r"\bCIG[:\s]*([A-Z0-9]{10})\b", re.IGNORECASE)
REGEX_CATEGORIA_SOA = re.compile(r"\b(OG|OS)\s*(\d{1,2})(?:-([AB]))?\b", re.IGNORECASE)
REGEX_CLASSE = re.compile(r"\bClassifica[:\s]*(I{1,3}(?:-bis)?|IV(?:-bis)?|V{1,3}I{0,3})\b", re.IGNORECASE)

# Certificazioni
CERTIFICAZIONI_RILEVANTI = [
    "ISO 9001", "ISO 14001", "ISO 45001",
    "CAM", "Criteri Ambientali Minimi",
    "parità di genere", "white list", "SOA",
    "EMAS", "Ecolabel"
]

# Sezioni disciplinare
SEZIONI_DISCIPLINARE = {
    "oggetto": ["OGGETTO DELL'APPALTO", "IMPORTO E SUDDIVISIONE"],
    "durata": ["DURATA"],
    "requisiti_generali": ["REQUISITI DI ORDINE GENERALE"],
    "requisiti_speciali": ["REQUISITI DI ORDINE SPECIALE", "CAPACIT"],
    "criterio_aggiudicazione": ["CRITERIO DI AGGIUDICAZIONE"],
    "revisione_prezzi": ["REVISIONE PREZZI"],
    "subappalto": ["SUBAPPALTO"],
}
