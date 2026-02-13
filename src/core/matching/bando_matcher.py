from core.geo.province_db import get_provincia_coords
"""
Matcher Bandi-Imprese usando Supabase
"""
from supabase import create_client
from dotenv import load_dotenv
import os
from typing import List, Dict, Optional
from datetime import datetime
import json

load_dotenv()


class BandoMatcher:
    """
    Match bandi parsed con imprese in Supabase
    """
    
    def __init__(self):
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY devono essere in .env")
        
        self.supabase = create_client(url, key)
        print("✅ Matcher connesso a Supabase")
    
    def save_bando(self, bando_strutturato) -> str:
        """
        Salva bando parsed in Supabase
        
        Returns:
            bando_id (str)
        """
        
        print(f"\n💾 Salvataggio bando {bando_strutturato.cig}...")
        
        # Prepara payload (solo campi esistenti)
        categorie_str = ', '.join([f"{cat.categoria} {cat.classifica}" for cat in bando_strutturato.categorie])
        
        bando_data = {
            'cig': bando_strutturato.cig,
            'titolo': f"Bando {bando_strutturato.cig} - {categorie_str}",
            'stazione_appaltante': bando_strutturato.localizzazione.provincia or 'N/A',
            'descrizione_breve': f"PNRR: {'Sì' if bando_strutturato.pnrr else 'No'}. Importo: €{bando_strutturato.importi.totale_appalto:,.2f}. Categorie: {categorie_str}",
            'cpv_principale': None,
            'cpv_secondari': None,
            'tipologia': bando_strutturato.procedura.tipo,
            'regione': bando_strutturato.localizzazione.regione,
            'provincia': bando_strutturato.localizzazione.provincia
        }
        
        # Insert
        try:
            result = self.supabase.table('bandi').upsert(bando_data, on_conflict='cig').execute()
            bando_id = result.data[0]['id']
            print(f"  ✅ Bando salvato/aggiornato (ID: {bando_id})")
            return bando_id
        
        except Exception as e:
            print(f"  ❌ Errore salvataggio: {e}")
            raise
    
    def find_matching_imprese(self, bando_strutturato) -> List[Dict]:
        """
        Trova imprese che possono partecipare al bando
        
        Returns:
            Lista di imprese con match score
        """
        
        print(f"\n🔍 Ricerca imprese per bando {bando_strutturato.cig}...")
        
        # Step 1: Fetch tutte le imprese
        result = self.supabase.table('imprese').select('*').execute()
        imprese = result.data
        
        print(f"  📋 Trovate {len(imprese)} imprese nel DB")
        
        # Step 2: Match per ogni impresa
        matches = []
        
        for impresa in imprese:
            score = self._calculate_match_score(bando_strutturato, impresa)
            
            if score['total'] > 0:
                matches.append({
                    'impresa_id': impresa['id'],
                    'ragione_sociale': impresa['ragione_sociale'],
                    'score': score,
                    'can_participate': score['total'] >= 70,  # Soglia 70%
                    'missing_requirements': score['missing']
                })
        
        # Ordina per score
        matches.sort(key=lambda x: x['score']['total'], reverse=True)
        
        print(f"  ✅ Match completato: {len(matches)} imprese compatibili")
        
        return matches
    
    def _calculate_match_score(self, bando, impresa) -> Dict:
        """
        Calcola match score impresa vs bando
        
        Score breakdown:
        - Categorie SOA: 50 punti
        - Regione operativa: 20 punti
        - Importo capacità: 20 punti
        - Certificazioni: 10 punti
        """
        
        score = {
            'total': 0,
            'categorie': 0,
            'regione': 0,
            'importo': 0,
            'certificazioni': 0,
            'missing': []
        }
        
        # 1. Check categorie SOA (50 punti)
        attestazioni = impresa.get('attestazioni_soa', [])
        if not attestazioni:
            attestazioni = []
        
        # Normalizza classifica (I->I, II->II, III->III, etc)
        def normalize_classifica(c):
            """Converte numeri romani in uppercase"""
            return c.upper() if c else ''
        
        categorie_bando = {f"{cat.categoria}_{normalize_classifica(cat.classifica)}" for cat in bando.categorie}
        categorie_impresa = set()
        
        for att in attestazioni:
            if isinstance(att, dict):
                # Formato DB: {"codice": "OG1", "classe": "II"}
                codice = att.get('codice', '')
                classe = att.get('classe', '')
                if codice and classe:
                    categorie_impresa.add(f"{codice}_{classe}")
        
        if categorie_bando:
            matched = len(categorie_bando & categorie_impresa)
            total_required = len(categorie_bando)
            score['categorie'] = int((matched / total_required) * 50)
            
            if matched < total_required:
                missing_cat = categorie_bando - categorie_impresa
                score['missing'].extend([f"Categoria {cat}" for cat in missing_cat])
        else:
            score['categorie'] = 50  # No categorie specificate = ok
        
        # 2. Check regione (20 punti)
        regioni_impresa = impresa.get('regioni_operative', [])
        if bando.localizzazione.regione in regioni_impresa:
            score['regione'] = 20
        else:
            score['missing'].append(f"Opera in {bando.localizzazione.regione}")
        
        # 3. Check importo (20 punti)
        importo_min = impresa.get('importo_min_interesse', 0)
        importo_max = impresa.get('importo_max_capacita', 999999999)
        importo_bando = bando.importi.totale_appalto
        
        if importo_min <= importo_bando <= importo_max:
            score['importo'] = 20
        else:
            if importo_bando < importo_min:
                score['missing'].append(f"Importo troppo basso (<€{importo_min:,.0f})")
            else:
                score['missing'].append(f"Importo troppo alto (>€{importo_max:,.0f})")
        
        # 4. Certificazioni (10 punti bonus)
        if bando.pnrr:
            cert = impresa.get('certificazioni_possedute', [])
            if 'ISO 9001' in cert or 'ISO 14001' in cert:
                score['certificazioni'] = 10
        else:
            score['certificazioni'] = 10  # Non richieste
        
        # Total
        score['total'] = sum([
            score['categorie'],
            score['regione'],
            score['importo'],
            score['certificazioni']
        ])
        
        return score


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    import sys; sys.path.insert(0, "src"); from core.parsers.bando_parser import BandoParserUniversale
    
    print("\n" + "="*70)
    print("🧪 TEST MATCHER")
    print("="*70 + "\n")
    
    # Parse bando
    parser = BandoParserUniversale()
    bando = parser.parse('data/bandi/bando_test_pnrr.pdf')
    
    # Match
    matcher = BandoMatcher()
    
    # Salva bando
    bando_id = matcher.save_bando(bando)
    
    # Trova imprese
    matches = matcher.find_matching_imprese(bando)
    
    # Mostra top 5
    print("\n" + "="*70)
    print("🏆 TOP 5 IMPRESE MATCHATE")
    print("="*70 + "\n")
    
    for i, match in enumerate(matches[:5], 1):
        print(f"{i}. {match['ragione_sociale']}")
        print(f"   Score: {match['score']['total']}/100")
        print(f"   - Categorie: {match['score']['categorie']}/50")
        print(f"   - Regione: {match['score']['regione']}/20")
        print(f"   - Importo: {match['score']['importo']}/20")
        print(f"   - Certificazioni: {match['score']['certificazioni']}/10")
        
        if match['missing_requirements']:
            print(f"   ⚠️ Mancante: {', '.join(match['missing_requirements'])}")
        
        print(f"   {'✅ Può partecipare' if match['can_participate'] else '❌ Non idonea'}")
        print()