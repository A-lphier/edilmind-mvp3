"""
Parser Universale Bandi - Auto-detection + Fallback intelligente
"""
import re
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional, List, Tuple
from pydantic import BaseModel, Field
import json

# Unstructured
from unstructured.partition.pdf import partition_pdf


# ============================================================================
# MODELS
# ============================================================================

class Importi(BaseModel):
    totale_appalto: float = Field(default=0.0, ge=0)
    lavori: Optional[float] = None
    sicurezza: Optional[float] = None
    manodopera: Optional[float] = None
    progettazione: Optional[float] = None


class Categoria(BaseModel):
    categoria: str
    classifica: str
    importo: Optional[float] = None
    prevalente: bool = False
    sios: bool = False


class Localizzazione(BaseModel):
    provincia: Optional[str] = None
    regione: Optional[str] = None


class Procedura(BaseModel):
    tipo: str = "Aperta"
    criterio: str = "Prezzo più basso"


class BandoStrutturato(BaseModel):
    cig: Optional[str] = None
    cup: Optional[str] = None
    pnrr: bool = False
    importi: Importi
    categorie: List[Categoria] = []
    localizzazione: Localizzazione = Localizzazione()
    procedura: Procedura = Procedura()
    confidence_score: float = 0.0


# ============================================================================
# UTILITIES
# ============================================================================

def normalize_italian_number(text: str) -> float:
    """693.820,49 -> 693820.49"""
    if not text:
        return 0.0
    text = str(text).replace(' ', '').replace('€', '').strip()
    if '.' in text and ',' in text:
        text = text.replace('.', '').replace(',', '.')
    elif ',' in text:
        text = text.replace(',', '.')
    try:
        return float(text)
    except:
        return 0.0


def detect_pdf_type(pdf_path: str) -> str:
    """
    Rileva tipo PDF per scegliere strategy corretta
    
    Returns:
        'textual': PDF con testo estraibile (usa fast)
        'scanned': PDF scansionato (usa hi_res + OCR)
        'complex': Layout complesso (usa hi_res no OCR)
    """
    try:
        doc = fitz.open(pdf_path)
        
        # Campiona prima pagina
        page = doc[0]
        text = page.get_text()
        
        # Check 1: È scansione? (poco testo)
        if len(text.strip()) < 200:
            doc.close()
            return 'scanned'
        
        # Check 2: Layout complesso? (tante immagini/grafici)
        images = page.get_images()
        if len(images) > 5:
            doc.close()
            return 'complex'
        
        # Check 3: Testo pulito (default)
        doc.close()
        return 'textual'
        
    except Exception as e:
        print(f"⚠️ Errore detection: {e}, assumo 'textual'")
        return 'textual'


# ============================================================================
# PARSER UNIVERSALE
# ============================================================================

class BandoParserUniversale:
    """
    Parser che si adatta automaticamente al tipo di PDF
    """
    
    def __init__(self):
        self.tesseract_available = self._check_tesseract()
        print(f"✅ Parser Universale inizializzato")
        print(f"   Tesseract OCR: {'✅ Disponibile' if self.tesseract_available else '❌ Non disponibile (solo PDF testuali)'}")
    
    def _check_tesseract(self) -> bool:
        """Verifica se Tesseract è installato"""
        import shutil
        return shutil.which('tesseract') is not None
    
    def parse(self, pdf_path: str) -> BandoStrutturato:
        """
        Parse con auto-detection
        """
        
        print(f"\n{'='*70}")
        print(f"🔍 PARSING: {Path(pdf_path).name}")
        print(f"{'='*70}\n")
        
        # STEP 1: Rileva tipo PDF
        pdf_type = detect_pdf_type(pdf_path)
        print(f"📋 Tipo PDF rilevato: {pdf_type.upper()}")
        
        # STEP 2: Scegli strategy
        if pdf_type == 'scanned':
            if not self.tesseract_available:
                print("⚠️ PDF scansionato ma Tesseract non disponibile, provo 'fast'")
                strategy = 'fast'
            else:
                strategy = 'hi_res'
        elif pdf_type == 'complex':
            strategy = 'hi_res' if self.tesseract_available else 'fast'
        else:
            strategy = 'fast'
        
        print(f"⚙️ Strategy Unstructured: {strategy}")
        
        # STEP 3A: Estrai testo grezzo con PyMuPDF (per regex precise)
        print(f"📄 Estrazione testo grezzo (PyMuPDF)...")
        doc = fitz.open(pdf_path)
        raw_text = "\n".join([page.get_text() for page in doc])
        doc.close()
        print(f"✅ Estratti {len(raw_text)} caratteri")
        
        # STEP 3B: Parse con Unstructured (per struttura/tabelle)
        try:
            print(f"📄 Unstructured partition (struttura)...")
            
            elements = partition_pdf(
                filename=pdf_path,
                strategy=strategy,
                infer_table_structure=True
            )
            
            print(f"✅ Estratti {len(elements)} elementi strutturati")
            
        except Exception as e:
            print(f"⚠️ Unstructured fallito: {e}")
            elements = []
        
        # STEP 4: Tabelle da Unstructured
        tables = [el for el in elements if hasattr(el, 'category') and el.category == "Table"]
        print(f"📊 Trovate {len(tables)} tabelle")
        
        # Usa raw_text per extraction (più affidabile)
        full_text = raw_text
        
        # STEP 5: Extract dati
        cig, cup = self._extract_cig_cup(full_text)
        pnrr = self._extract_pnrr(full_text)
        importi = self._extract_importi(full_text)
        categorie = self._extract_categorie(full_text)
        localizzazione = self._extract_localizzazione(full_text)
        
        # STEP 6: Confidence
        confidence = self._calculate_confidence(cig, importi, categorie)
        
        bando = BandoStrutturato(
            cig=cig,
            cup=cup,
            pnrr=pnrr,
            importi=importi,
            categorie=categorie,
            localizzazione=localizzazione,
            confidence_score=confidence
        )
        
        print(f"\n{'='*70}")
        print(f"✅ PARSING COMPLETATO (confidence: {confidence:.0%})")
        print(f"{'='*70}")
        
        return bando
    
    def _extract_cig_cup(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        cig_match = re.search(r'\bCIG[:\s]*([A-Z0-9]{10})\b', text, re.I)
        cup_match = re.search(r'\bCUP[:\s]*([A-Z0-9]{15})\b', text, re.I)
        
        cig = cig_match.group(1) if cig_match else None
        cup = cup_match.group(1) if cup_match else None
        
        if cig:
            print(f"  ✅ CIG: {cig}")
        if cup:
            print(f"  ✅ CUP: {cup}")
        
        return cig, cup
    
    def _extract_pnrr(self, text: str) -> bool:
        is_pnrr = 'PNRR' in text or 'NextGeneration' in text or 'Next Generation' in text
        if is_pnrr:
            print(f"  ✅ PNRR: Sì 🇪🇺")
        return is_pnrr
    
    def _extract_importi(self, text: str) -> Importi:
        print(f"\n💰 Estrazione importi...")
        
        # Totale - cerca "ammonta a € XXX"
        totale_match = re.search(r'ammonta\s+a\s+€\s*([\d.,]+)', text, re.I | re.DOTALL)
        totale = normalize_italian_number(totale_match.group(1)) if totale_match else 0.0
        if totale > 0:
            print(f"  ✅ Importo totale: €{totale:,.2f}")
        
        # Lavori - pattern con a capo: "IMPORTO ESECUZ. LAVORI:\n693.820,49"
        lavori_match = re.search(r'IMPORTO\s+ESECUZ\.\s+LAVORI:\s*([\d.,]+)', text, re.I | re.DOTALL)
        lavori = normalize_italian_number(lavori_match.group(1)) if lavori_match else None
        if lavori:
            print(f"  ✅ Lavori: €{lavori:,.2f}")
        
        # Progettazione - pattern con a capo
        prog_match = re.search(r'IMPORTO\s+PROGETTAZIONE.*?PROGETTAZ\.\s*([\d.,]+)', text, re.I | re.DOTALL)
        progettazione = normalize_italian_number(prog_match.group(1)) if prog_match else None
        if progettazione:
            print(f"  ✅ Progettazione: €{progettazione:,.2f}")
        
        # Sicurezza
        sic_match = re.search(r'di\s+cui\s+oneri\s+della\s+sicurezza\s+non\s+soggetti\s+a\s+ribasso\s*([\d.,]+)', text, re.I | re.DOTALL)
        sicurezza = normalize_italian_number(sic_match.group(1)) if sic_match else None
        if sicurezza:
            print(f"  ✅ Sicurezza: €{sicurezza:,.2f}")
        
        # Manodopera
        man_match = re.search(r'di\s+cui\s+costi\s+della\s+manodopera\s*([\d.,]+)', text, re.I | re.DOTALL)
        manodopera = normalize_italian_number(man_match.group(1)) if man_match else None
        if manodopera:
            print(f"  ✅ Manodopera: €{manodopera:,.2f}")
        
        # Fallback
        if totale == 0 and lavori:
            totale = lavori + (progettazione or 0)
            print(f"  ⚠️ Totale calcolato: €{totale:,.2f}")
        
        return Importi(
            totale_appalto=totale,
            lavori=lavori,
            sicurezza=sicurezza,
            manodopera=manodopera,
            progettazione=progettazione
        )
    
    def _extract_categorie(self, text: str) -> List[Categoria]:
        print(f"\n📂 Estrazione categorie SOA...")
        
        categorie = []
        
        # Pattern robusto
        pattern = r'\b(OG|OS|OGS)(\d+)\s+classifica\s+([IVX]+)\b'
        
        for match in re.finditer(pattern, text, re.I):
            tipo = match.group(1).upper()
            numero = match.group(2)
            classifica = match.group(3).upper()
            
            # Context analysis
            context = text[max(0, match.start()-100):match.end()+100]
            
            cat = Categoria(
                categoria=f"{tipo}{numero}",
                classifica=classifica,
                prevalente='prevalente' in context.lower(),
                sios='SIOS' in context or 'sios' in context.lower()
            )
            
            categorie.append(cat)
            
            flags = []
            if cat.prevalente:
                flags.append("PREVALENTE")
            if cat.sios:
                flags.append("SIOS")
            
            print(f"  ✅ {cat.categoria} {cat.classifica}" + 
                  (f" [{', '.join(flags)}]" if flags else ""))
        
        # Deduplicazione
        seen = set()
        unique_categorie = []
        for cat in categorie:
            key = (cat.categoria, cat.classifica)
            if key not in seen:
                seen.add(key)
                unique_categorie.append(cat)
        
        return unique_categorie
    
    def _extract_localizzazione(self, text: str) -> Localizzazione:
        # Province principali
        province = {
            'Roma': 'Lazio', 'Milano': 'Lombardia', 'Napoli': 'Campania',
            'Torino': 'Piemonte', 'Palermo': 'Sicilia', 'Genova': 'Liguria',
            'Bologna': 'Emilia-Romagna', 'Firenze': 'Toscana', 'Bari': 'Puglia'
        }
        
        for prov, reg in province.items():
            if prov in text:
                return Localizzazione(provincia=prov, regione=reg)
        
        return Localizzazione()
    
    def _calculate_confidence(self, cig, importi, categorie) -> float:
        score = 0.0
        if cig:
            score += 0.3
        if importi.totale_appalto > 0:
            score += 0.4
        if categorie:
            score += 0.3
        return min(score, 1.0)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("❌ Usage: python bando_parser.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    parser = BandoParserUniversale()
    bando = parser.parse(pdf_path)
    
    print(f"\n📊 JSON OUTPUT:")
    print("="*70)
    print(json.dumps(bando.model_dump(), indent=2, ensure_ascii=False, default=str))