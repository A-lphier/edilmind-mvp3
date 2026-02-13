"""
EdilMind - Database Manager (Supabase)
"""
from supabase import create_client, Client
from typing import Dict, List
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import SUPABASE_URL, SUPABASE_KEY

# Client Supabase
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"⚠️  Errore connessione Supabase: {e}")

# ==============================================================================
# SCHEMA SQL - COPIA ED ESEGUI SU SUPABASE SQL EDITOR
# ==============================================================================
SCHEMA_SQL = """
-- EdilMind Database Schema

CREATE EXTENSION IF NOT EXISTS vector;

-- Tabella bandi
CREATE TABLE IF NOT EXISTS bandi (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cig VARCHAR(10) UNIQUE NOT NULL,
    titolo TEXT,
    stazione_appaltante TEXT,
    descrizione_breve TEXT,
    cpv_principale VARCHAR(20),
    cpv_secondari JSONB,
    tipologia VARCHAR(50),
    
    -- Territorio
    regione VARCHAR(50),
    provincia VARCHAR(50),
    comune TEXT,
    nuts VARCHAR(10),
    
    -- Importi
    importo_base_gara NUMERIC(15, 2),
    oneri_sicurezza NUMERIC(15, 2),
    importo_complessivo NUMERIC(15, 2),
    
    -- Timing
    durata_mesi INTEGER,
    scadenza_offerte TIMESTAMPTZ,
    
    -- Requisiti
    categorie_soa JSONB,
    certificazioni_richieste JSONB,
    
    -- Criterio
    criterio_tipo VARCHAR(20),
    peso_tecnica INTEGER,
    peso_economica INTEGER,
    formula_punteggio VARCHAR(20),
    
    -- Flags
    revisione_prezzi BOOLEAN DEFAULT FALSE,
    stato VARCHAR(20) DEFAULT 'attivo',
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indici
CREATE INDEX IF NOT EXISTS idx_bandi_cig ON bandi(cig);
CREATE INDEX IF NOT EXISTS idx_bandi_regione ON bandi(regione);
CREATE INDEX IF NOT EXISTS idx_bandi_scadenza ON bandi(scadenza_offerte);
CREATE INDEX IF NOT EXISTS idx_bandi_importo ON bandi(importo_base_gara);
CREATE INDEX IF NOT EXISTS idx_bandi_stato ON bandi(stato);

-- Tabella sezioni (per RAG)
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
    attestazioni_soa JSONB,
    certificazioni_possedute JSONB,
    regioni_operative JSONB,
    importo_min_interesse NUMERIC(15, 2),
    importo_max_capacita NUMERIC(15, 2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

def print_schema():
    """Stampa schema SQL da copiare."""
    print("\n" + "="*80)
    print("📋 SCHEMA SQL - COPIA ED ESEGUI SU SUPABASE")
    print("="*80 + "\n")
    print(SCHEMA_SQL)
    print("\n" + "="*80)

def insert_bando(metadata: Dict) -> str:
    """Inserisce bando nel DB."""
    if not supabase:
        print("⚠️  Supabase non configurato - skipping insert")
        return None
    
    data = {
        "cig": metadata["cig"],
        "titolo": metadata.get("titolo", "Bando senza titolo"),
        "descrizione_breve": metadata.get("descrizione_breve"),
        "cpv_principale": metadata["cpv_codes"][0] if metadata.get("cpv_codes") else None,
        "cpv_secondari": metadata.get("cpv_codes", [])[1:],
        "regione": metadata.get("regione"),
        "importo_base_gara": metadata["importi"].get("base_gara"),
        "oneri_sicurezza": metadata["importi"].get("oneri_sicurezza"),
        "importo_complessivo": metadata["importi"].get("complessivo"),
        "durata_mesi": metadata.get("durata_mesi"),
        "scadenza_offerte": metadata.get("scadenza_offerte"),
        "categorie_soa": metadata.get("categorie_soa", []),
        "certificazioni_richieste": metadata.get("certificazioni_richieste", []),
        "revisione_prezzi": metadata.get("revisione_prezzi", False),
        "criterio_tipo": metadata.get("criterio_aggiudicazione", {}).get("tipo"),
        "peso_tecnica": metadata.get("criterio_aggiudicazione", {}).get("peso_tecnica"),
        "peso_economica": metadata.get("criterio_aggiudicazione", {}).get("peso_economica"),
    }
    
    try:
        result = supabase.table("bandi").upsert(data).execute()
        bando_id = result.data[0]["id"]
        print(f"✓ Bando inserito: {bando_id}")
        return bando_id
    except Exception as e:
        print(f"❌ Errore inserimento: {e}")
        return None

def insert_sections(bando_id: str, sections: Dict[str, str]):
    """Inserisce sezioni testuali."""
    if not supabase or not bando_id:
        return
    
    records = []
    for section_name, content in sections.items():
        if content and section_name != "full_text" and len(content) > 50:
            records.append({
                "bando_id": bando_id,
                "section_name": section_name,
                "content": content[:10000],
            })
    
    if records:
        try:
            supabase.table("bandi_sections").insert(records).execute()
            print(f"✓ {len(records)} sezioni inserite")
        except Exception as e:
            print(f"⚠️  Errore inserimento sezioni: {e}")

if __name__ == "__main__":
    print_schema()
