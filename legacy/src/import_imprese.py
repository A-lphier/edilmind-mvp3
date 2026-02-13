"""Import imprese da CSV SOA"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "core"))

import csv
import json
from dotenv import load_dotenv

# Carica .env ESPLICITAMENTE
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from core.database import supabase

# Mapping province -> regioni
PROVINCE_REGIONI = {
    "ROMA": "Lazio", "MILANO": "Lombardia", "NAPOLI": "Campania",
    "TORINO": "Piemonte", "GENOVA": "Liguria", "VENEZIA": "Veneto",
    "BOLOGNA": "Emilia-Romagna", "FIRENZE": "Toscana", "BARI": "Puglia",
    "CATANIA": "Sicilia", "PALERMO": "Sicilia", "CAGLIARI": "Sardegna",
    "ANCONA": "Marche", "PERUGIA": "Umbria", "TRENTO": "Trentino-Alto Adige",
    "BOLZANO": "Trentino-Alto Adige", "AOSTA": "Valle d Aosta"
}

def import_csv(csv_path):
    if not supabase:
        print("❌ Supabase non configurato!")
        print("Verifica il file .env")
        return
    
    print(f"📂 Caricamento {csv_path}...")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"✓ {len(rows)} righe trovate")
    
    # Filtra solo attestati VALIDI
    rows_valide = [r for r in rows if r.get("attestato_stato") in ["PUBBLICO", "SOSTITUITO"]]
    print(f"✓ {len(rows_valide)} imprese con attestati validi")
    
    # Raggruppa per impresa (stesso codice fiscale)
    imprese_dict = {}
    
    for row in rows_valide:
        cf = row["impresa_codice_fiscale"]
        
        if cf not in imprese_dict:
            provincia = row["provincia_nome"]
            regione = PROVINCE_REGIONI.get(provincia, provincia)
            
            imprese_dict[cf] = {
                "ragione_sociale": row["impresa_denominazione"],
                "attestazioni_soa": [],
                "certificazioni_possedute": [],
                "regioni_operative": [regione],
                "importo_min_interesse": 50000,
                "importo_max_capacita": 1000000,
            }
        
        # Aggiungi categorie SOA
        try:
            categorie = json.loads(row["categorie_soa"])
            for cat in categorie:
                imprese_dict[cf]["attestazioni_soa"].append({
                    "codice": cat["categoria"],
                    "classe": cat["classifica"],
                    "descrizione": ""
                })
        except:
            pass
    
    imprese = list(imprese_dict.values())
    
    print(f"\n💾 Inserimento {len(imprese)} imprese uniche...")
    
    try:
        # Insert in batch
        batch_size = 50  # Ridotto per evitare timeout
        inserted = 0
        errors = 0
        
        for i in range(0, len(imprese), batch_size):
            batch = imprese[i:i+batch_size]
            try:
                result = supabase.table("imprese").insert(batch).execute()
                inserted += len(result.data)
                print(f"  ✓ {inserted}/{len(imprese)} inserite...")
            except Exception as e:
                errors += len(batch)
                print(f"  ⚠️  Batch {i}-{i+len(batch)} saltato: {str(e)[:50]}")
        
        print(f"\n✅ Totale: {inserted} imprese importate!")
        if errors > 0:
            print(f"⚠️  {errors} imprese saltate (probabilmente duplicate)")
        
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python src/import_imprese.py <file.csv>")
    else:
        import_csv(sys.argv[1])
