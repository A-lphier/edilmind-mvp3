"""
RAG Engine - Core del sistema di Retrieval Augmented Generation
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

class RAGEngine:
    """
    Engine principale per il sistema RAG di EdilMind
    Gestisce indicizzazione, retrieval e risposta con LLM
    """
    
    def __init__(self, kb_path: str = "data/knowledge_base", use_supabase: bool = False):
        """
        Inizializza RAG Engine
        
        Args:
            kb_path: Path alla knowledge base
            use_supabase: Se True usa Supabase, altrimenti locale
        """
        self.kb_path = Path(kb_path)
        self.use_supabase = use_supabase
        self.documents = []
        self.metadata = {}
        
        print(f"✅ RAGEngine inizializzato (KB: {kb_path}, Supabase: {use_supabase})")
        
        # Carica documenti esistenti
        self._load_documents()
    
    def _load_documents(self):
        """Carica documenti dalla knowledge base"""
        if not self.kb_path.exists():
            print(f"⚠️  Knowledge base non trovata: {self.kb_path}")
            self.kb_path.mkdir(parents=True, exist_ok=True)
            return
        
        # Scan ricorsivo
        doc_count = 0
        for ext in ['.txt', '.md', '.pdf', '.docx']:
            files = list(self.kb_path.rglob(f'*{ext}'))
            doc_count += len(files)
            
            for file_path in files:
                self.documents.append({
                    'path': str(file_path),
                    'name': file_path.name,
                    'type': ext[1:],
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        print(f"📚 Caricati {doc_count} documenti dalla KB")
    
    def search(self, query: str, top_k: int = 5, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Ricerca nella knowledge base
        
        Args:
            query: Query di ricerca
            top_k: Numero massimo di risultati
            filters: Filtri opzionali (categoria, provincia, etc)
        
        Returns:
            Lista di risultati con contenuto e metadata
        """
        print(f"🔍 Ricerca: '{query}' (top_k={top_k})")
        
        # Per ora ritorna documenti disponibili (mock)
        results = []
        
        for doc in self.documents[:top_k]:
            # Leggi contenuto (solo per .txt e .md per ora)
            content = ""
            if doc['type'] in ['txt', 'md']:
                try:
                    with open(doc['path'], 'r', encoding='utf-8') as f:
                        content = f.read()[:500]  # Prime 500 char
                except Exception as e:
                    content = f"[Errore lettura: {e}]"
            
            results.append({
                'content': content,
                'metadata': {
                    'source': doc['name'],
                    'path': doc['path'],
                    'type': doc['type'],
                    'relevance_score': 0.85  # Mock score
                }
            })
        
        print(f"  ✅ Trovati {len(results)} risultati")
        return results
    

    
    def query(self, query: str, top_k: int = 5, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Alias per search() - usato da app.py
        
        Args:
            query: Query di ricerca
            top_k: Numero massimo di risultati
            filters: Filtri opzionali
        
        Returns:
            Lista di risultati (stesso formato di search())
        """
        return self.search(query=query, top_k=top_k, filters=filters)

    
    def build_context(self, search_results: List[Dict[str, Any]], max_tokens: int = 3000) -> str:
        """
        Costruisce contesto per LLM dai risultati di ricerca
        
        Args:
            search_results: Risultati da search() o query()
            max_tokens: Limite token (~4 char per token)
        
        Returns:
            Stringa formattata con contesto per LLM
        """
        if not search_results:
            return "Nessun documento rilevante trovato nella Knowledge Base."
        
        context_parts = []
        char_limit = max_tokens * 4  # Approssimazione: 1 token ≈ 4 caratteri
        current_chars = 0
        
        for i, result in enumerate(search_results, 1):
            source = result.get('metadata', {}).get('source', 'Documento sconosciuto')
            content = result.get('content', '')
            score = result.get('metadata', {}).get('relevance_score', 0)
            
            # Formato output
            doc_header = f"\n--- DOCUMENTO {i}: {source} (Rilevanza: {score:.2f}) ---\n"
            doc_content = content[:1000]  # Max 1000 char per documento
            
            section = doc_header + doc_content
            
            # Check limite
            if current_chars + len(section) > char_limit:
                context_parts.append("\n[...altri documenti omessi per limite token...]")
                break
            
            context_parts.append(section)
            current_chars += len(section)
        
        final_context = "\n".join(context_parts)
        
        print(f"📝 Contesto costruito: {len(search_results)} documenti, {current_chars} caratteri")
        
        return final_context
    def add_document(self, file_path: str, metadata: Optional[Dict] = None) -> bool:
        """
        Aggiungi documento alla knowledge base
        
        Args:
            file_path: Path del file da aggiungere
            metadata: Metadata opzionali
        
        Returns:
            True se successo, False altrimenti
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                print(f"❌ File non trovato: {file_path}")
                return False
            
            # Copia in KB
            dest_path = self.kb_path / file_path.name
            
            if dest_path.exists():
                print(f"⚠️  File già esistente: {dest_path.name}")
                return False
            
            # Copia file
            import shutil
            shutil.copy2(file_path, dest_path)
            
            # Aggiungi a lista documenti
            self.documents.append({
                'path': str(dest_path),
                'name': dest_path.name,
                'type': dest_path.suffix[1:],
                'size': dest_path.stat().st_size,
                'modified': datetime.now().isoformat(),
                'metadata': metadata or {}
            })
            
            print(f"✅ Documento aggiunto: {dest_path.name}")
            return True
            
        except Exception as e:
            print(f"❌ Errore aggiunta documento: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Ottieni statistiche sulla knowledge base
        
        Returns:
            Dict con statistiche
        """
        total_size = sum(doc['size'] for doc in self.documents)
        
        types = {}
        for doc in self.documents:
            doc_type = doc['type']
            types[doc_type] = types.get(doc_type, 0) + 1
        
        return {
            'total_documents': len(self.documents),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'document_types': types,
            'kb_path': str(self.kb_path),
            'use_supabase': self.use_supabase
        }
    
    def clear_cache(self):
        """Pulisci cache (se presente)"""
        print("🧹 Cache pulita")
        pass

# ============================================================================
# TEST STANDALONE
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TEST RAG ENGINE")
    print("="*60 + "\n")
    
    # Init
    rag = RAGEngine()
    
    # Stats
    stats = rag.get_stats()
    print(f"\n📊 Statistiche KB:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # Test search
    print("\n" + "-"*60)
    results = rag.search("appalti pubblici", top_k=3)
    
    print(f"\n📄 Risultati ricerca:")
    for i, res in enumerate(results, 1):
        print(f"\n{i}. {res['metadata']['source']}")
        print(f"   Tipo: {res['metadata']['type']}")
        print(f"   Score: {res['metadata']['relevance_score']}")
        print(f"   Preview: {res['content'][:100]}...")
    
    print("\n" + "="*60)
    print("✅ Test completato")
    print("="*60 + "\n")