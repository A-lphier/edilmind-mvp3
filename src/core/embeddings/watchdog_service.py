"""
src/core/embeddings/watchdog_service.py
Servizio watchdog per auto-vettorializzazione documenti
"""
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from core.rag.rag_engine import RAGEngine

logger = logging.getLogger(__name__)

class KBWatcher(FileSystemEventHandler):
    """Handler eventi filesystem"""
    
    def __init__(self, rag_engine: RAGEngine):
        self.rag = rag_engine
        self.processing = set()
    
    def on_created(self, event):
        """Trigger su nuovo file"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Solo file supportati
        if file_path.suffix.lower() not in {'.pdf', '.docx', '.txt', '.md'}:
            return
        
        if str(file_path) in self.processing:
            return
        
        logger.info(f"🆕 Nuovo file: {file_path.name}")
        self.processing.add(str(file_path))
        
        try:
            time.sleep(2)  # Attendi scrittura completa
            
            # Determina categoria da path
            category = self._detect_category(file_path)
            
            # Parse & add
            text = self._parse_file(file_path)
            metadata = {
                'filename': file_path.name,
                'titolo': file_path.stem.replace('_', ' ')
            }
            
            self.rag.add_document(text, category, metadata)
            logger.info(f"  ✅ {file_path.name} vettorializzato")
        
        except Exception as e:
            logger.error(f"  ❌ Errore: {e}")
        
        finally:
            self.processing.discard(str(file_path))
    
    def _detect_category(self, path: Path) -> str:
        """Auto-detect categoria"""
        path_str = str(path).lower()
        
        if 'normative' in path_str:
            return 'normative'
        elif 'circolar' in path_str:
            return 'circolari'
        elif 'giurisprudenza' in path_str:
            return 'giurisprudenza'
        elif 'tecnic' in path_str:
            return 'tecniche'
        else:
            return 'normative'
    
    def _parse_file(self, path: Path) -> str:
        """Parse file multi-formato"""
        if path.suffix == '.pdf':
            import PyMuPDF as fitz
            doc = fitz.open(path)
            text = "\n".join([p.get_text() for p in doc])
            doc.close()
            return text
        elif path.suffix == '.docx':
            from docx import Document
            doc = Document(path)
            return "\n".join([p.text for p in doc.paragraphs])
        else:
            return path.read_text(encoding='utf-8')


def start_watchdog(kb_root: str = "data/knowledge_base"):
    """Avvia watchdog service"""
    logger.info("🚀 Avvio Watchdog Service...")
    
    rag = RAGEngine()
    handler = KBWatcher(rag)
    observer = Observer()
    
    # Monitora tutte le sottocartelle
    kb_path = Path(kb_root)
    for subdir in kb_path.iterdir():
        if subdir.is_dir():
            observer.schedule(handler, str(subdir), recursive=True)
            logger.info(f"  👁️  {subdir.name}")
    
    observer.start()
    logger.info("✅ Watchdog attivo!")
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_watchdog()