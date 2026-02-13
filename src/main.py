"""
EdilMind - CLI Entry Point
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "core"))

import json
from core.parser import parse_pdf
from core.extraction import extract_metadata_completo
from core.database import insert_bando, print_schema

def process_bando(pdf_path: Path, metadata_extra: dict = None) -> str:
    """Pipeline completa."""
    print(f"\n{'='*80}")
    print(f"🚀 PROCESSING: {pdf_path.name}")
    print(f"{'='*80}\n")
    
    text = parse_pdf(pdf_path)
    if not text:
        print("❌ Errore parsing PDF")
        return None
    
    print("🔍 Estrazione metadati...")
    metadata = extract_metadata_completo(text)
    
    if metadata_extra:
        metadata.update(metadata_extra)
    
    if not metadata.get("cig"):
        import uuid
        metadata["cig"] = str(uuid.uuid4())[:10].upper()
    
    print("💾 Salvataggio database...")
    bando_id = insert_bando(metadata)
    
    print(f"\n{'='*80}")
    print("📊 RIEPILOGO")
    print(f"{'='*80}")
    print(f"CIG:              {metadata['cig']}")
    print(f"Titolo:           {metadata.get('titolo', 'N/D')[:70]}")
    print(f"CPV:              {', '.join(metadata['cpv_codes'][:3]) or 'N/D'}")
    print(f"Importo base:     €{metadata['importi']['base_gara']:,.2f}" if metadata['importi']['base_gara'] else "Importo:          N/D")
    print(f"Categorie SOA:    {len(metadata['categorie_soa'])}")
    print(f"Certificazioni:   {', '.join(metadata['certificazioni_richieste']) or 'Nessuna'}")
    print(f"{'='*80}\n")
    
    return bando_id

def main():
    if len(sys.argv) < 2:
        print("""
╔════════════════════════════════════════════════════════════╗
║               EDILMIND - Sistema Matching Bandi            ║
╚════════════════════════════════════════════════════════════╝

COMANDI:

  python src\main.py process <pdf_path> [--regione X]
      Processa un bando da PDF

  python src\main.py schema
      Mostra schema SQL per Supabase

  python src\main.py ui
      Avvia interfaccia web Streamlit

  python src\main.py test
      Test configurazione
        """)
        return
    
    comando = sys.argv[1]
    
    if comando == "process":
        if len(sys.argv) < 3:
            print("❌ Specifica il PDF")
            return
        
        pdf_path = Path(sys.argv[2])
        if not pdf_path.exists():
            print(f"❌ File non trovato: {pdf_path}")
            return
        
        metadata_extra = {}
        for i in range(3, len(sys.argv), 2):
            if i+1 < len(sys.argv):
                if sys.argv[i] == "--regione":
                    metadata_extra["regione"] = sys.argv[i+1]
        
        process_bando(pdf_path, metadata_extra)
    
    elif comando == "schema":
        print_schema()
    
    elif comando == "ui":
        import subprocess
        print("\n🚀 Avvio interfaccia Streamlit...\n")
        subprocess.run(["streamlit", "run", "src/ui/app.py"])
    
    elif comando == "test":
        print("\n🧪 Test configurazione\n")
        print("="*60)
        
        from core.config import SUPABASE_URL, SUPABASE_KEY
        
        print(f"✓ Python: {sys.version.split()[0]}")
        print(f"✓ Directory: {Path.cwd()}")
        
        if SUPABASE_URL and SUPABASE_URL != "https://xxx.supabase.co":
            print(f"✓ Supabase URL OK")
        else:
            print(f"⚠️  Supabase URL non configurato")
        
        print("\n" + "="*60)
        print("\nPROSSIMI PASSI:")
        print("1. Modifica .env")
        print("2. python src\main.py schema")
        print("3. python src\main.py ui (Avvia interfaccia web)")
        print("4. python src\main.py process data\pdf_bandi\bando.pdf")
        print()
    
    else:
        print(f"❌ Comando sconosciuto: {comando}")

if __name__ == "__main__":
    main()
