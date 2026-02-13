"""
EdilMind - Parser PDF semplificato (PyPDF2)
"""
import PyPDF2
from pathlib import Path
from typing import Dict
import sys
sys.path.insert(0, str(Path(__file__).parent))

def parse_pdf_simple(pdf_path: Path) -> str:
    """Estrae testo grezzo da PDF."""
    print(f"📄 Parsing {pdf_path.name}...")
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text_parts = []
            
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            full_text = "\n".join(text_parts)
            print(f"✓ Estratto testo da {len(reader.pages)} pagine ({len(full_text)} caratteri)")
            return full_text
    
    except Exception as e:
        print(f"❌ Errore parsing PDF: {e}")
        return ""

if __name__ == "__main__":
    print("✓ Modulo parser_simple caricato")
