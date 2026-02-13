"""
EdilMind - Estrazione metadati
"""
import re
from typing import Dict, List, Optional
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import *

def extract_cig(text: str) -> Optional[str]:
    match = REGEX_CIG.search(text)
    return match.group(1) if match else None

def extract_cpv_codes(text: str) -> List[str]:
    return list(set(REGEX_CPV.findall(text)))

def parse_importo(text: str) -> Optional[float]:
    try:
        clean = text.replace(".", "").replace(",", ".")
        return float(clean)
    except:
        return None

def extract_importi(text: str) -> Dict[str, Optional[float]]:
    importi = {"base_gara": None, "oneri_sicurezza": None, "complessivo": None}
    lines = text.split("\n")
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        if any(k in line_lower for k in ["base di gara", "base d'asta", "importo a base"]):
            for j in range(max(0, i-2), min(len(lines), i+3)):
                match = REGEX_IMPORTO.search(lines[j])
                if match:
                    importi["base_gara"] = parse_importo(match.group(2))
                    break
        
        if "oneri" in line_lower and "sicurezza" in line_lower:
            match = REGEX_IMPORTO.search(line)
            if match:
                importi["oneri_sicurezza"] = parse_importo(match.group(2))
        
        if "complessivo" in line_lower or ("totale" in line_lower and "importo" in line_lower):
            match = REGEX_IMPORTO.search(line)
            if match:
                importi["complessivo"] = parse_importo(match.group(2))
    
    return importi

def extract_categorie_soa(text: str) -> List[Dict]:
    categorie = []
    seen = set()
    
    for match in REGEX_CATEGORIA_SOA.finditer(text):
        tipo = match.group(1)
        numero = match.group(2)
        suffisso = match.group(3) or ""
        cod = f"{tipo}{numero}{'-' + suffisso if suffisso else ''}"
        
        if cod in seen:
            continue
        seen.add(cod)
        
        context = text[max(0, match.start()-150):min(len(text), match.end()+150)]
        classe_match = REGEX_CLASSE.search(context)
        
        categorie.append({
            "codice": cod,
            "classe": classe_match.group(1) if classe_match else None,
            "descrizione": CATEGORIE_SOA.get(cod, "Non catalogata")
        })
    
    return categorie

def extract_certificazioni(text: str) -> List[str]:
    found = set()
    text_lower = text.lower()
    for cert in CERTIFICAZIONI_RILEVANTI:
        if cert.lower() in text_lower:
            found.add(cert)
    return list(found)

def extract_durata(text: str) -> Optional[int]:
    mesi = re.search(r"(\d+)\s*mes[ei]", text, re.IGNORECASE)
    if mesi:
        return int(mesi.group(1))
    anni = re.search(r"(\d+)\s*ann[oi]", text, re.IGNORECASE)
    if anni:
        return int(anni.group(1)) * 12
    return None

def extract_stazione_appaltante(text: str) -> Optional[str]:
    """Estrae nome stazione appaltante."""
    patterns = [
        r"Stazione\s+[Aa]ppaltante[:\s]+([^\n]+)",
        r"Amministrazione\s+aggiudicatrice[:\s]+([^\n]+)",
        r"Ente[:\s]+([^\n]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def extract_titolo(text: str) -> Optional[str]:
    """Estrae titolo bando."""
    lines = text.split("\n")[:20]
    for line in lines:
        line = line.strip()
        if len(line) > 30 and len(line) < 200:
            if any(k in line.lower() for k in ["appalto", "affidamento", "lavori", "servizi"]):
                return line
    return None

def extract_metadata_completo(text: str) -> Dict:
    """Estrazione completa."""
    return {
        "cig": extract_cig(text),
        "titolo": extract_titolo(text),
        "stazione_appaltante": extract_stazione_appaltante(text),
        "cpv_codes": extract_cpv_codes(text),
        "importi": extract_importi(text),
        "categorie_soa": extract_categorie_soa(text),
        "certificazioni_richieste": extract_certificazioni(text),
        "durata_mesi": extract_durata(text),
        "revisione_prezzi": "revisione prezzi" in text.lower(),
        "criterio_aggiudicazione": {
            "tipo": "OEPV" if "economicamente" in text.lower() else "prezzo",
            "peso_tecnica": None,
            "peso_economica": None
        }
    }
