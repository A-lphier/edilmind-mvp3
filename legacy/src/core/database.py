"""
EdilMind - Database Manager
"""
from supabase import create_client, Client
from typing import Dict, List, Optional
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL != "https://xxx.supabase.co":
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"⚠️  Errore Supabase: {e}")

SCHEMA_SQL = """
-- EdilMind Database Schema v2.0

CREATE EXTENSION IF NOT EXISTS vector;

-- Tabella bandi
CREATE TABLE IF NOT EXISTS bandi (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cig VARCHAR(10) UNIQUE NOT NULL,
    titolo TEXT,
    stazione_appaltante TEXT,
    descrizione_breve TEXT,
    cpv_principale VARCHAR(20),
    cpv_secondari JSONB DEFAULT '[]',
    tipologia VARCHAR(50),
    regione VARCHAR(50),
    provincia VARCHAR(50),
    comune TEXT,
    nuts VARCHAR(10),
    importo_base_gara NUMERIC(15, 2),
    oneri_sicurezza NUMERIC(15, 2),
    importo_complessivo NUMERIC(15, 2),
    durata_mesi INTEGER,
    scadenza_offerte TIMESTAMPTZ,
    categorie_soa JSONB DEFAULT '[]',
    certificazioni_richieste JSONB DEFAULT '[]',
    criterio_tipo VARCHAR(20) DEFAULT 'OEPV',
    peso_tecnica INTEGER,
    peso_economica INTEGER,
    formula_punteggio VARCHAR(20),
    revisione_prezzi BOOLEAN DEFAULT FALSE,
    subappalto_max_perc INTEGER,
    stato VARCHAR(20) DEFAULT 'attivo',
    link_piattaforma TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bandi_cig ON bandi(cig);
CREATE INDEX IF NOT EXISTS idx_bandi_regione ON bandi(regione);
CREATE INDEX IF NOT EXISTS idx_bandi_scadenza ON bandi(scadenza_offerte);
CREATE INDEX IF NOT EXISTS idx_bandi_importo ON bandi(importo_base_gara);
CREATE INDEX IF NOT EXISTS idx_bandi_stato ON bandi(stato);

-- Tabella sezioni
CREATE TABLE IF NOT EXISTS bandi_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bando_id UUID REFERENCES bandi(id) ON DELETE CASCADE,
    section_name VARCHAR(100),
    content TEXT,
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sections_bando ON bandi_sections(bando_id);

-- Funzione ricerca vettoriale
CREATE OR REPLACE FUNCTION match_sections(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    bando_id UUID,
    section_name VARCHAR,
    content TEXT,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        bs.bando_id,
        bs.section_name,
        bs.content,
        1 - (bs.embedding <=> query_embedding) AS similarity
    FROM bandi_sections bs
    WHERE 1 - (bs.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

-- Tabella profili imprese
CREATE TABLE IF NOT EXISTS imprese (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ragione_sociale VARCHAR(255) NOT NULL,
    attestazioni_soa JSONB DEFAULT '[]',
    certificazioni_possedute JSONB DEFAULT '[]',
    regioni_operative JSONB DEFAULT '[]',
    fatturato_ultimo_anno NUMERIC(15, 2),
    fatturato_triennio NUMERIC(15, 2),
    importo_min_interesse NUMERIC(15, 2) DEFAULT 50000,
    importo_max_capacita NUMERIC(15, 2),
    cel_lavori_analoghi JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- View bandi attivi
CREATE OR REPLACE VIEW bandi_attivi AS
SELECT 
    b.*,
    CASE 
        WHEN b.scadenza_offerte > NOW() THEN 'aperto'
        WHEN b.scadenza_offerte <= NOW() THEN 'scaduto'
        ELSE 'n/d'
    END as status_scadenza
FROM bandi b
WHERE b.stato = 'attivo'
ORDER BY b.scadenza_offerte ASC NULLS LAST;
"""

def print_schema():
    """Stampa schema SQL."""
    print("\n" + "="*80)
    print("📋 SCHEMA SQL - COPIA ED ESEGUI SU SUPABASE SQL EDITOR")
    print("="*80 + "\n")
    print(SCHEMA_SQL)
    print("\n" + "="*80)

def insert_bando(metadata: Dict) -> Optional[str]:
    """Inserisce bando."""
    if not supabase:
        return None
    
    data = {
        "cig": metadata["cig"],
        "titolo": metadata.get("titolo", "Bando senza titolo"),
        "stazione_appaltante": metadata.get("stazione_appaltante"),
        "descrizione_breve": metadata.get("descrizione_breve"),
        "cpv_principale": metadata.get("cpv_codes", [None])[0] if metadata.get("cpv_codes") else None,
        "cpv_secondari": metadata.get("cpv_codes", [])[1:],
        "regione": metadata.get("regione"),
        "provincia": metadata.get("provincia"),
        "importo_base_gara": metadata.get("importi", {}).get("base_gara"),
        "oneri_sicurezza": metadata.get("importi", {}).get("oneri_sicurezza"),
        "importo_complessivo": metadata.get("importi", {}).get("complessivo"),
        "durata_mesi": metadata.get("durata_mesi"),
        "scadenza_offerte": metadata.get("scadenza_offerte"),
        "categorie_soa": metadata.get("categorie_soa", []),
        "certificazioni_richieste": metadata.get("certificazioni_richieste", []),
        "revisione_prezzi": metadata.get("revisione_prezzi", False),
        "criterio_tipo": metadata.get("criterio_aggiudicazione", {}).get("tipo", "OEPV"),
        "peso_tecnica": metadata.get("criterio_aggiudicazione", {}).get("peso_tecnica"),
        "peso_economica": metadata.get("criterio_aggiudicazione", {}).get("peso_economica"),
    }
    
    try:
        result = supabase.table("bandi").upsert(data).execute()
        return result.data[0]["id"]
    except Exception as e:
        import traceback
        print(f"❌ Errore insert dettagliato: {e}")
        print(f"📊 Dati inviati:")
        import json
        print(json.dumps(data, indent=2, default=str))
        traceback.print_exc()
        return None

def get_bandi_attivi(limit: int = 50) -> List[Dict]:
    """Recupera bandi attivi."""
    if not supabase:
        return []
    try:
        result = supabase.table("bandi_attivi").select("*").limit(limit).execute()
        return result.data
    except:
        return []

def insert_impresa(profilo: Dict) -> Optional[str]:
    """Inserisce profilo impresa."""
    if not supabase:
        return None
    try:
        result = supabase.table("imprese").insert(profilo).execute()
        return result.data[0]["id"]
    except Exception as e:
        print(f"❌ Errore insert impresa: {e}")
        return None

if __name__ == "__main__":
    print_schema()
