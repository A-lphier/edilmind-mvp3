"""
Script ingest Knowledge Base Legal-Grade
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.rag.rag_handler import LegalRAGHandler


def main():
    print("\n" + "="*70)
    print("🚀 EDILMIND - INGEST KNOWLEDGE BASE LEGAL-GRADE")
    print("="*70)
    print("\n📋 Features:")
    print("   • Parsing structure-aware (Unstructured.io)")
    print("   • Citation tracking (pagina + sezione)")
    print("   • Hybrid Search ready (Vector + BM25)")
    print("   • Metadata extraction avanzata")
    
    try:
        rag = LegalRAGHandler(kb_dir="data/kb")
        rag.ingest_all()
        
        print("\n" + "="*70)
        print("✅ KNOWLEDGE BASE PRONTA!")
        print("="*70)
        print("\n🎯 Test query:")
        print("   python -c \"from src.core.rag.rag_handler import LegalRAGHandler; rag = LegalRAGHandler(); print(rag.query_with_citations('Cosa sono le categorie SOA?'))\"")
        print("\n🎯 Oppure usa Streamlit:")
        print("   streamlit run src/ui/app.py")
        print("")
        
    except Exception as e:
        print(f"\n❌ ERRORE: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()