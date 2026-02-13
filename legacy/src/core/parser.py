"""
EdilMind - Parser PDF
"""
import PyPDF2
from pathlib import Path
from typing import Optional

def parse_pdf(pdf_path: Path) -> Optional[str]:
    """Estrae testo da PDF."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n".join(text_parts)
    except Exception as e:
        print(f"❌ Errore parsing: {e}")
        return None
