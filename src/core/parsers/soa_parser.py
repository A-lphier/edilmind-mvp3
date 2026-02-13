"""
SOA Parser - Estrazione dati da Attestazioni SOA PDF
"""
import re
import fitz  # PyMuPDF
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

class SOAParser:
    """
    Parser per estrarre dati da PDF Attestazione SOA
    Supporta formati comuni degli organismi SOA italiani
    """
    
    # Pattern regex per estrazione dati
    PATTERNS = {
        'ragione_sociale': [
            r'Ragione\s+Sociale[:\s]+([A-Z][A-Z\s\.\,\&]+?)(?:\n|Sede)',
            r'(?:Impresa|Operatore|Società)[:\s]+([A-Z][A-Z\s\.\,\&]+?)(?:\n|P\.)',
            r'denominazione[:\s]+([A-Z][A-Z\s\.\,\&]+?)(?:\n|sede)',
        ],
        'partita_iva': [
            r'P\.?\s?IVA[:\s]+(\d{11})',
            r'Partita\s+IVA[:\s]+(\d{11})',
            r'C\.F\./P\.IVA[:\s]+(\d{11})',
        ],
        'categoria': [
            r'\b(OG\d{1,2}|OS\d{1,2}|OG \d{1,2}|OS \d{1,2})\b',
            r'Categoria[:\s]+(OG\d{1,2}|OS\d{1,2})',
        ],
        'classifica': [
            r'\b(I{1,3}|IV|V|VI{1,2}|VIII|I-bis)\b(?=\s|$)',
            r'Classifica[:\s]+(I{1,3}|IV|V|VI{1,2}|VIII)',
        ],
        'scadenza': [
            r'(?:Scadenza|Validità|valida fino al)[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})',
            r'(?:fino al|entro il)[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})',
        ],
        'organismo_soa': [
            r'Organismo[:\s]+([A-Z][A-Z\s]+?)(?:\n|Via)',
            r'(?:rilasciata da|emessa da)[:\s]+([A-Z][A-Z\s]+)',
        ],
    }
    
    def __init__(self):
        """Inizializza parser"""
        print("✅ SOA Parser inizializzato")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Estrai testo da PDF usando PyMuPDF
        
        Args:
            pdf_path: Path del file PDF
        
        Returns:
            Testo estratto
        """
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text += page.get_text()
            
            doc.close()
            
            print(f"📄 Estratte {len(doc)} pagine da {Path(pdf_path).name}")
            return text
            
        except Exception as e:
            print(f"❌ Errore estrazione PDF: {e}")
            return ""
    
    def extract_categorie(self, text: str) -> List[Dict[str, str]]:
        """
        Estrai categorie SOA con classifiche
        
        Args:
            text: Testo del PDF
        
        Returns:
            Lista di dict {'categoria': 'OG1', 'classifica': 'III'}
        """
        categorie = []
        
        # Trova tutte le categorie
        cat_matches = []
        for pattern in self.PATTERNS['categoria']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            cat_matches.extend([(m.group(1).replace(' ', ''), m.start()) for m in matches])
        
        # Rimuovi duplicati mantenendo ordine
        seen = set()
        unique_cats = []
        for cat, pos in cat_matches:
            if cat not in seen:
                seen.add(cat)
                unique_cats.append((cat, pos))
        
        # Per ogni categoria, cerca classifica vicina
        for categoria, cat_pos in unique_cats:
            # Cerca classifica nei 200 caratteri successivi
            context = text[cat_pos:cat_pos+200]
            
            classifica = None
            for pattern in self.PATTERNS['classifica']:
                match = re.search(pattern, context)
                if match:
                    classifica = match.group(1)
                    break
            
            categorie.append({
                'categoria': categoria,
                'classifica': classifica or 'N/A'
            })
        
        return categorie
    
    def parse(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parsing completo di un PDF SOA
        
        Args:
            pdf_path: Path del file PDF
        
        Returns:
            Dict con tutti i dati estratti
        """
        print(f"\n🔍 Parsing SOA: {Path(pdf_path).name}")
        
        # Estrai testo
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text:
            return {
                'success': False,
                'error': 'Impossibile estrarre testo dal PDF'
            }
        
        # Estrai dati
        result = {
            'success': True,
            'file_name': Path(pdf_path).name,
            'parsed_at': datetime.now().isoformat(),
        }
        
        # Ragione Sociale
        for pattern in self.PATTERNS['ragione_sociale']:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                result['ragione_sociale'] = match.group(1).strip()
                break
        
        # Partita IVA
        for pattern in self.PATTERNS['partita_iva']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['partita_iva'] = match.group(1)
                break
        
        # Categorie e Classifiche
        result['categorie'] = self.extract_categorie(text)
        
        # Scadenza
        for pattern in self.PATTERNS['scadenza']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['scadenza'] = match.group(1)
                break
        
        # Organismo SOA
        for pattern in self.PATTERNS['organismo_soa']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['organismo_soa'] = match.group(1).strip()
                break
        
        # Valida risultato
        if not result.get('ragione_sociale') and not result.get('categorie'):
            result['success'] = False
            result['error'] = 'Dati insufficienti estratti. Verificare formato PDF.'
        
        return result
    
    def format_output(self, parsed_data: Dict[str, Any]) -> str:
        """
        Formatta output per visualizzazione
        
        Args:
            parsed_data: Dati estratti
        
        Returns:
            Stringa formattata
        """
        if not parsed_data.get('success'):
            return f"❌ Errore: {parsed_data.get('error', 'Parsing fallito')}"
        
        output = []
        output.append("="*60)
        output.append("📋 ATTESTAZIONE SOA - DATI ESTRATTI")
        output.append("="*60)
        
        if 'ragione_sociale' in parsed_data:
            output.append(f"\n🏢 Ragione Sociale: {parsed_data['ragione_sociale']}")
        
        if 'partita_iva' in parsed_data:
            output.append(f"🔢 Partita IVA: {parsed_data['partita_iva']}")
        
        if parsed_data.get('categorie'):
            output.append(f"\n📂 Categorie Qualificate ({len(parsed_data['categorie'])}):")
            for cat in parsed_data['categorie']:
                output.append(f"   • {cat['categoria']} - Classifica {cat['classifica']}")
        
        if 'scadenza' in parsed_data:
            output.append(f"\n📅 Scadenza: {parsed_data['scadenza']}")
        
        if 'organismo_soa' in parsed_data:
            output.append(f"🏛️  Organismo: {parsed_data['organismo_soa']}")
        
        output.append("\n" + "="*60)
        
        return "\n".join(output)


# ============================================================================
# TEST STANDALONE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*60)
    print("🧪 TEST SOA PARSER")
    print("="*60 + "\n")
    
    parser = SOAParser()
    
    # Test con file esempio
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        
        if Path(pdf_path).exists():
            result = parser.parse(pdf_path)
            print(parser.format_output(result))
            
            # Output JSON
            import json
            print("\n📄 JSON Output:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"❌ File non trovato: {pdf_path}")
    else:
        print("💡 Uso: python soa_parser.py <path_to_soa.pdf>")
        print("\nEsempio:")
        print("  python src/core/parsers/soa_parser.py attestazione_soa.pdf")
    
    print("\n" + "="*60)