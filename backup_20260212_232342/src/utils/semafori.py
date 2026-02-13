"""
EdilMind - Sistema Semafori
"""
from typing import Dict, Tuple, List
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from config import CLASSI_IMPORTI_MAX

def check_soa_compatibility(categorie_richieste: List[Dict], attestazioni: List[Dict]) -> bool:
    """Verifica compatibilità SOA."""
    if not categorie_richieste:
        return True
    
    soa_map = {att["codice"]: att for att in attestazioni}
    
    for cat in categorie_richieste:
        codice = cat["codice"]
        if codice not in soa_map:
            return False
        
        classe_rich = cat.get("classe")
        if classe_rich:
            classe_imp = soa_map[codice].get("classe")
            if not is_classe_sufficiente(classe_imp, classe_rich):
                return False
    
    return True

def is_classe_sufficiente(classe_impresa: str, classe_richiesta: str) -> bool:
    """Confronta classi SOA."""
    ordine = ["I", "II", "III", "III-bis", "IV", "IV-bis", "V", "VI", "VII", "VIII"]
    try:
        idx_imp = ordine.index(classe_impresa)
        idx_rich = ordine.index(classe_richiesta)
        return idx_imp >= idx_rich
    except ValueError:
        return False

def semaforo_legale(bando: Dict, profilo_impresa: Dict) -> Tuple[str, str]:
    """Semaforo legale."""
    issues = []
    
    soa_ok = check_soa_compatibility(
        bando.get("categorie_soa", []),
        profilo_impresa.get("attestazioni_soa", [])
    )
    
    if not soa_ok:
        issues.append("SOA insufficiente - Richiede avvalimento/RTI")
    
    cert_rich = set(bando.get("certificazioni_richieste", []))
    cert_poss = set(profilo_impresa.get("certificazioni_possedute", []))
    cert_mancanti = cert_rich - cert_poss
    
    if cert_mancanti:
        issues.append(f"Certificazioni mancanti: {', '.join(cert_mancanti)}")
    
    importo = bando.get("importo_base_gara", 0)
    max_classe = max([
        CLASSI_IMPORTI_MAX.get(att.get("classe", "I"), 0)
        for att in profilo_impresa.get("attestazioni_soa", [{"classe": "I"}])
    ])
    
    if importo > max_classe:
        issues.append(f"Importo supera capacità SOA")
        return ("ROSSO", "; ".join(issues))
    
    if not issues:
        return ("VERDE", "Tutti requisiti soddisfatti")
    else:
        return ("GIALLO", "; ".join(issues))

def semaforo_economico(bando: Dict) -> Tuple[str, str]:
    """Semaforo economico (semplificato)."""
    importo = bando.get("importo_base_gara", 0)
    
    if importo < 100000:
        return ("GIALLO", "Importo basso - Margini ridotti")
    elif importo > 5000000:
        return ("GIALLO", "Importo alto - Rischio maggiore")
    else:
        return ("VERDE", "Importo gestibile")

def genera_report_semafori(bando: Dict, profilo_impresa: Dict) -> Dict:
    """Report completo."""
    legale_colore, legale_msg = semaforo_legale(bando, profilo_impresa)
    economico_colore, economico_msg = semaforo_economico(bando)
    
    if legale_colore == "ROSSO":
        raccomandazione = "❌ NON PARTECIPARE"
    elif legale_colore == "VERDE" and economico_colore == "VERDE":
        raccomandazione = "✅ PARTECIPA"
    else:
        raccomandazione = "⚡ VALUTA CON ATTENZIONE"
    
    return {
        "cig": bando.get("cig"),
        "titolo": bando.get("titolo"),
        "semaforo_legale": {"colore": legale_colore, "messaggio": legale_msg},
        "semaforo_economico": {"colore": economico_colore, "messaggio": economico_msg},
        "raccomandazione": raccomandazione,
        "importo": bando.get("importo_base_gara"),
        "scadenza": bando.get("scadenza_offerte"),
    }
