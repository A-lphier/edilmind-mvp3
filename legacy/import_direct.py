"""Import imprese da CSV SOA - Versione standalone"""
import csv
import json
from supabase import create_client

# Credenziali
SUPABASE_URL = "https://rnhtupovjqvlmsmnvosg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJuaHR1cG92anF2bG1zbW52b3NnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA4OTk2NDIsImV4cCI6MjA4NjQ3NTY0Mn0.N-oT_yPE9teFzPcV_q8r-_Sirm9PmpY6r58jDeY_rgU"

print("🔌 Connessione a Supabase...")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✓ Connesso!")

# Mapping province
PROVINCE_REGIONI = {
    "ROMA": "Lazio", "MILANO": "Lombardia", "NAPOLI": "Campania",
    "TORINO": "Piemonte", "GENOVA": "Liguria", "VENEZIA": "Veneto",
    "BOLOGNA": "Emilia-Romagna", "FIRENZE": "Toscana", "BARI": "Puglia",
    "CATANIA": "Sicilia", "PALERMO": "Sicilia", "CAGLIARI": "Sardegna",
    "ANCONA": "Marche", "PERUGIA": "Umbria", "TRENTO": "Trentino-Alto Adige"
}

def import_csv(csv_path):
    print(f"\n📂 Caricamento {csv_path}...")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"✓ {len(rows)} righe trovate")
    
    # Filtra attestati validi
    rows_valide = [r for r in rows if r.get("attestato_stato") in ["PUBBLICO", "SOSTITUITO"]]
    print(f"✓ {len(rows_valide)} imprese con attestati validi")
    
    # Raggruppa per CF
    imprese_dict = {}
    
    for row in rows_valide:
        cf = row["impresa_codice_fiscale"]
        
        if cf not in imprese_dict:
            provincia = row["provincia_nome"]
            regione = PROVINCE_REGIONI.get(provincia, provincia)
            
            imprese_dict[cf] = {
                "ragione_sociale": row["impresa_denominazione"][:255],
                "attestazioni_soa": [],
                "certificazioni_possedute": [],
                "regioni_operative": [regione],
                "importo_min_interesse": 50000,
                "importo_max_capacita": 1000000,
            }
        
        # SOA
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
    
    # Insert in batch
    batch_size = 50
    inserted = 0
    errors = 0
    
    for i in range(0, len(imprese), batch_size):
        batch = imprese[i:i+batch_size]
        try:
            result = supabase.table("imprese").insert(batch).execute()
            inserted += len(result.data)
            if (i // batch_size) % 20 == 0:
                print(f"  ✓ {inserted}/{len(imprese)} inserite...")
        except Exception as e:
            errors += len(batch)
            if "duplicate" not in str(e).lower():
                print(f"  ⚠️  Errore: {str(e)[:60]}")
    
    print(f"\n✅ Import completato!")
    print(f"   Inserite: {inserted}")
    print(f"   Saltate: {errors}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python import_direct.py <file.csv>")
    else:
        import_csv(sys.argv[1])
