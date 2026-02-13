"""
ANAC Scraper - Bandi dalla Banca Dati Nazionale Contratti Pubblici
Aggiornato con 107 Province Italiane
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json
import time
import re
import sys
from pathlib import Path

# Import database province
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from data.province_italia import PROVINCE_ITALIA, get_province_by_regione, get_regioni_list

class ANACScraper:
    """
    Scraper per bandi ANAC con database completo province italiane
    Fonte: https://dati.anticorruzione.it/opendata
    """
    
    BASE_URL = "https://dati.anticorruzione.it/api/3/action"
    
    def __init__(self):
        """Inizializza scraper ANAC"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EdilMind/1.0 (Scraper Bandi Pubblici)'
        })
        print(f"✅ ANAC Scraper inizializzato ({len(PROVINCE_ITALIA)} province)")
    
    def search_bandi(self, 
                     regione: Optional[str] = None,
                     provincia: Optional[str] = None,
                     categoria: Optional[str] = None,
                     importo_min: Optional[float] = None,
                     importo_max: Optional[float] = None,
                     giorni_scadenza: int = 90,
                     limit: int = 50) -> List[Dict[str, Any]]:
        """
        Cerca bandi aperti
        
        Args:
            regione: Regione (es. 'Lombardia')
            provincia: Provincia specifica (es. 'Milano')
            categoria: Categoria lavori (es. 'OG1')
            importo_min: Importo minimo in euro
            importo_max: Importo massimo in euro
            giorni_scadenza: Bandi in scadenza nei prossimi N giorni
            limit: Numero massimo risultati
        
        Returns:
            Lista bandi
        """
        print(f"\n🔍 Ricerca bandi ANAC (limit: {limit})...")
        if regione:
            print(f"   Regione: {regione}")
        if provincia:
            print(f"   Provincia: {provincia}")
        
        # Per ora mock - TODO: API ANAC reale
        bandi = self._generate_mock_bandi(
            regione=regione,
            provincia=provincia,
            categoria=categoria,
            importo_min=importo_min,
            importo_max=importo_max,
            limit=limit
        )
        
        print(f"  ✅ Trovati {len(bandi)} bandi")
        
        return bandi
    
    def _generate_mock_bandi(self, 
                            regione: Optional[str] = None,
                            provincia: Optional[str] = None,
                            categoria: Optional[str] = None,
                            importo_min: Optional[float] = None,
                            importo_max: Optional[float] = None,
                            limit: int = 50) -> List[Dict[str, Any]]:
        """
        Genera bandi mock realistici usando database 107 province
        """
        import random
        
        # Usa tutte le regioni o filtra
        regioni_disponibili = get_regioni_list()
        
        if regione:
            regioni_target = [regione] if regione in regioni_disponibili else regioni_disponibili[:3]
        else:
            regioni_target = random.sample(regioni_disponibili, min(8, len(regioni_disponibili)))
        
        categorie = ['OG1', 'OG3', 'OG6', 'OG11', 'OS6', 'OS28', 'OS30']
        classifiche = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']
        
        tipi_lavori = [
            'Ristrutturazione edificio scolastico',
            'Manutenzione straordinaria viabilità comunale',
            'Costruzione nuovo edificio polifunzionale',
            'Riqualificazione energetica immobili comunali',
            'Adeguamento sismico scuola elementare',
            'Realizzazione parcheggio pubblico',
            'Manutenzione stradale ordinaria',
            'Costruzione centro sportivo',
            'Opere urbanizzazione lottizzazione',
            'Rifacimento copertura edificio pubblico',
            'Ampliamento scuola media',
            'Restauro centro storico',
            'Realizzazione impianto fotovoltaico',
            'Bonifica area industriale dismessa',
            'Riqualificazione piazza comunale',
        ]
        
        stazioni = [
            'Comune di {}',
            'Provincia di {}',
            'Unione Comuni {}',
            'Comunità Montana {}',
        ]
        
        bandi = []
        
        for i in range(limit):
            # Seleziona regione
            reg = random.choice(regioni_target)
            
            # Ottieni province della regione dal database
            province_reg = get_province_by_regione(reg)
            
            if not province_reg:
                continue
            
            # Filtra per provincia se specificata
            if provincia and provincia in province_reg:
                prov_nome = provincia
            else:
                prov_nome = random.choice(province_reg)
            
            prov_dati = PROVINCE_ITALIA[prov_nome]
            
            cat = categoria if categoria else random.choice(categorie)
            
            # Importo per categoria
            importo_ranges = {
                'OG1': (150000, 5000000),
                'OG3': (200000, 10000000),
                'OG6': (100000, 3000000),
                'OG11': (80000, 2000000),
                'OS6': (50000, 800000),
                'OS28': (40000, 600000),
                'OS30': (60000, 1500000),
            }
            
            min_imp, max_imp = importo_ranges.get(cat, (100000, 2000000))
            
            if importo_min:
                min_imp = max(min_imp, importo_min)
            if importo_max:
                max_imp = min(max_imp, importo_max)
            
            importo = random.randint(int(min_imp), int(max_imp))
            
            # Scadenza
            giorni_mancanti = random.randint(10, 90)
            scadenza = datetime.now() + timedelta(days=giorni_mancanti)
            
            # CIG realistico
            cig = f"{random.randint(1000000, 9999999):07d}{random.randint(10, 99)}"
            
            bando = {
                'id': f"bando_{i+1}_{cig}",
                'cig': cig,
                'titolo': f"{random.choice(tipi_lavori)} - {prov_nome}",
                'stazione_appaltante': random.choice(stazioni).format(prov_nome),
                'importo': importo,
                'importo_str': f"€ {importo:,.2f}",
                'categoria': cat,
                'classifica': random.choice(classifiche),
                'regione': reg,
                'provincia': prov_nome,
                'provincia_sigla': prov_dati['sigla'],
                'comune': prov_nome,
                'scadenza': scadenza.strftime('%d/%m/%Y'),
                'scadenza_iso': scadenza.isoformat(),
                'giorni_scadenza': giorni_mancanti,
                'tipo_procedura': random.choice(['Aperta', 'Negoziata', 'Affidamento Diretto']),
                'criterio': random.choice(['Offerta economicamente più vantaggiosa', 'Prezzo più basso']),
                'url': f"https://www.anticorruzione.it/gara/{cig}",
                'estratto_at': datetime.now().isoformat(),
                'fonte': 'ANAC OpenData (Mock)',
                # Coordinate reali dal database + variazione casuale
                'lat': prov_dati['lat'] + random.uniform(-0.05, 0.05),
                'lon': prov_dati['lon'] + random.uniform(-0.05, 0.05),
            }
            
            bandi.append(bando)
        
        return bandi
    
    def get_bando_details(self, cig: str) -> Optional[Dict[str, Any]]:
        """
        Ottieni dettagli completi di un bando
        
        Args:
            cig: Codice CIG
        
        Returns:
            Dict con dettagli bando
        """
        print(f"📄 Recupero dettagli bando CIG: {cig}")
        
        # Mock per ora
        return {
            'cig': cig,
            'descrizione_completa': 'Dettagli completi del bando...',
            'documenti': [
                {'tipo': 'Bando', 'url': f'https://example.com/bando_{cig}.pdf'},
                {'tipo': 'Disciplinare', 'url': f'https://example.com/disc_{cig}.pdf'},
            ],
            'requisiti': {
                'categoria': 'OG1',
                'classifica': 'III',
                'certificazioni': ['ISO 9001', 'ISO 14001'],
            }
        }
    
    def export_to_json(self, bandi: List[Dict], output_path: str):
        """
        Esporta bandi in JSON
        
        Args:
            bandi: Lista bandi
            output_path: Path file output
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'updated_at': datetime.now().isoformat(),
                'count': len(bandi),
                'bandi': bandi
            }, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Esportati {len(bandi)} bandi in: {output_path}")


# ============================================================================
# TEST STANDALONE
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 TEST ANAC SCRAPER - 107 PROVINCE")
    print("="*70 + "\n")
    
    scraper = ANACScraper()
    
    # Test 1: Regione specifica
    print("\n📍 TEST 1: Lombardia")
    bandi_lombardia = scraper.search_bandi(regione='Lombardia', limit=5)
    
    for i, bando in enumerate(bandi_lombardia, 1):
        print(f"{i}. {bando['provincia']} ({bando['provincia_sigla']}) - {bando['titolo'][:50]}")
    
    # Test 2: Provincia specifica
    print("\n📍 TEST 2: Milano")
    bandi_milano = scraper.search_bandi(provincia='Milano', limit=3)
    
    for i, bando in enumerate(bandi_milano, 1):
        print(f"{i}. {bando['titolo']}")
        print(f"   Importo: {bando['importo_str']}")
        print(f"   Coordinate: {bando['lat']:.4f}, {bando['lon']:.4f}")
    
    # Test 3: Mix regioni
    print("\n📍 TEST 3: Regioni diverse")
    for regione in ['Sicilia', 'Toscana', 'Veneto']:
        bandi = scraper.search_bandi(regione=regione, limit=2)
        print(f"\n  {regione}:")
        for b in bandi:
            print(f"    • {b['provincia']} ({b['provincia_sigla']})")
    
    # Export
    import os
    os.makedirs('data/bandi', exist_ok=True)
    
    all_bandi = scraper.search_bandi(limit=20)
    scraper.export_to_json(all_bandi, 'data/bandi/bandi_italia.json')
    
    print("\n" + "="*70)
    print("✅ Test completato - 107 Province attive!")
    print("="*70)