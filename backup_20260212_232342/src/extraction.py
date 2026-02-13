"""
EdilMind - Estrazione metadati da testo strutturato
"""
import re
from typing import Dict, List, Optional
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import *

def extract_cig(text: str) -> Optional[str]:
    """Estrae CIG."""
    match = REGEX_CIG.search(text)
    return match.group(1) if match else None

def extract_cpv_codes(text: str) -> List[str]:
    """Estrae codici CPV."""
    return list(set(REGEX_CPV.findall(text)))

def parse_importo(text: str) -> Optional[float]:
    """Converte stringa importo in float."""
    try:
        clean = text.replace(".", "").replace(",", ".")
        return float(clean)
    except:
        return None

def extract_importi(text: str) -> Dict[str, Optional[float]]:
    """Estrae importi dal testo."""
    importi = {"base_gara": None, "oneri_sicurezza": None, "complessivo": None}
    
    lines = text.split("\n")
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Base d'asta
        if "base di gara" in line_lower or "base d'asta" in line_lower or "importo a base" in line_lower:
            for j in range(max(0, i-2), min(len(lines), i+3)):
                match = REGEX_IMPORTO.search(lines[j])
                if match:
                    importi["base_gara"] = parse_importo(match.group(2))
                    break
        
        # Oneri sicurezza
        if "oneri" in line_lower and "sicurezza" in line_lower:
            match = REGEX_IMPORTO.search(line)
            if match:
                importi["oneri_sicurezza"] = parse_importo(match.group(2))
        
        # Complessivo
        if "complessivo" in line_lower or "totale" in line_lower:
            match = REGEX_IMPORTO.search(line)
            if match:
                importi["complessivo"] = parse_importo(match.group(2))
    
    return importi

def extract_categorie_soa(text: str) -> List[Dict]:
    """Estrae categorie SOA."""
    categorie = []
    seen = set()
    
    for match in REGEX_CATEGORIA_SOA.finditer(text):
        tipo = match.group(1)
        numero = match.group(2)
        cod = f"{tipo}{numero}"
        
        if cod in seen:
            continue
        seen.add(cod)
        
        # Cerca classe nelle vicinanze
        context = text[max(0, match.start()-150):min(len(text), match.end()+150)]
        classe_match = REGEX_CLASSE.search(context)
        
        categorie.append({
            "codice": cod,
            "classe": classe_match.group(1) if classe_match else None,
            "descrizione": CATEGORIE_SOA.get(cod, "Non catalogata")
        })
    
    return categorie

def extract_certificazioni(text: str) -> List[str]:
    """Rileva certificazioni."""
    found = set()
    text_lower = text.lower()
    
    for cert in CERTIFICAZIONI_RILEVANTI:
        if cert.lower() in text_lower:
            found.add(cert)
    
    return list(found)

def extract_durata(text: str) -> Optional[int]:
    """Estrae durata in mesi."""
    mesi = re.search(r"(\d+)\s*mes[ei]", text, re.IGNORECASE)
    if mesi:
        return int(mesi.group(1))
    
    anni = re.search(r"(\d+)\s*ann[oi]", text, re.IGNORECASE)
    if anni:
        return int(anni.group(1)) * 12
    
    return None

def extract_metadata_completo(text: str) -> Dict:
    """Estrazione completa metadati."""
    
    return {
        "cig": extract_cig(text),
        "cpv_codes": extract_cpv_codes(text),
        "importi": extract_importi(text),
        "categorie_soa": extract_categorie_soa(text),
        "certificazioni_richieste": extract_certificazioni(text),
        "durata_mesi": extract_durata(text),
        "revisione_prezzi": "revisione prezzi" in text.lower(),
        "criterio_aggiudicazione": {
            "tipo": "OEPV" if "economicamente pi vantaggiosa" in text.lower() else "prezzo",
            "peso_tecnica": None,
            "peso_economica": None
        }
    }

if __name__ == "__main__":
    print("✓ Modulo extraction caricato")
