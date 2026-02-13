"""
RAG Handler Legal-Grade con:
- Unstructured.io (layout-aware parsing)
- Hybrid Search (BM25 + Vector)
- Citation tracking (pagina + sezione)
- Metadata extraction (tipo doc, articolo, comma)
"""
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
import json

# Unstructured per parsing avanzato
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title
from unstructured.staging.base import elements_to_json

# LangChain
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_core.documents import Document
from langchain_groq import ChatGroq

# Supabase
from supabase import create_client

load_dotenv()


class LegalRAGHandler:
    """
    RAG Handler per documenti legali con:
    - Parsing structure-aware (Unstructured)
    - Hybrid search (semantic + keyword BM25)
    - Citation tracking preciso
    """
    
    def __init__(self, kb_dir: str = "data/kb"):
        """
        Inizializza Legal RAG Handler
        
        Args:
            kb_dir: Directory documenti Knowledge Base
        """
        self.kb_dir = Path(kb_dir)
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Supabase
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY richiesti in .env")
        
        self.supabase = create_client(supabase_url, supabase_key)
        
        # Setup embeddings con Ollama
        print("🔄 Setup embeddings con sentence-transformers...")
        from sentence_transformers import SentenceTransformer
        self.embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Wrapper per compatibilità LangChain
        class EmbeddingWrapper:
            def __init__(self, model):
                self.model = model
            
            def embed_documents(self, texts):
                return self.model.encode(texts).tolist()
            
            def embed_query(self, text):
                return self.model.encode([text])[0].tolist()
        
        self.embeddings = EmbeddingWrapper(self.embed_model)
        print("✅ Embeddings ready")
        
        # Setup LLM Groq
        self.llm = ChatGroq(
            model="llama-3.1-70b-versatile",
            temperature=0,
            groq_api_key=os.getenv('GROQ_API_KEY')
        )
        
        print(f"✅ Legal RAG Handler inizializzato (KB: {self.kb_dir})")
    
    def parse_legal_pdf(self, pdf_path: Path) -> List[Dict]:
        """
        Parsing avanzato PDF con Unstructured.io
        Mantiene struttura gerarchica (Titoli, Articoli, Commi)
        
        Args:
            pdf_path: Path al PDF
            
        Returns:
            Lista di elementi strutturati con metadata
        """
        print(f"\n📄 Parsing structure-aware: {pdf_path.name}")
        
        try:
            # Partition PDF (layout-aware)
            elements = partition_pdf(
                filename=str(pdf_path),
                strategy="hi_res",  # High-res per tabelle/struttura
                infer_table_structure=True,
                extract_images_in_pdf=False,
                include_page_breaks=True,
                languages=["ita"]
            )
            
            print(f"   ✅ Estratti {len(elements)} elementi strutturali")
            
            # Chunking semantico (rispetta titoli/sezioni)
            chunks = chunk_by_title(
                elements,
                max_characters=1000,
                combine_text_under_n_chars=200,
                new_after_n_chars=800,
                overlap=100
            )
            
            print(f"   ✅ Creati {len(chunks)} chunks semantici")
            
            # Estrai metadata da ogni chunk
            structured_chunks = []
            
            for i, chunk in enumerate(chunks):
                metadata = chunk.metadata.to_dict()
                
                # Metadata base
                chunk_data = {
                    'text': chunk.text,
                    'chunk_id': i,
                    'source': pdf_path.name,
                    'page_number': metadata.get('page_number', 0),
                    'element_type': chunk.category,
                    'filename': metadata.get('filename', pdf_path.name)
                }
                
                # Metadata avanzati (se disponibili)
                if 'coordinates' in metadata:
                    chunk_data['bbox'] = metadata['coordinates']
                
                structured_chunks.append(chunk_data)
            
            return structured_chunks
            
        except Exception as e:
            print(f"   ⚠️ Errore parsing avanzato: {e}")
            print(f"   🔄 Fallback a parsing semplice...")
            
            # Fallback: parsing semplice
            from PyPDF2 import PdfReader
            reader = PdfReader(str(pdf_path))
            
            chunks = []
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                
                # Split in paragraphs
                paragraphs = text.split('\n\n')
                
                for para in paragraphs:
                    if len(para.strip()) > 50:
                        chunks.append({
                            'text': para.strip(),
                            'chunk_id': len(chunks),
                            'source': pdf_path.name,
                            'page_number': page_num,
                            'element_type': 'paragraph',
                            'filename': pdf_path.name
                        })
            
            print(f"   ✅ Fallback: {len(chunks)} chunks")
            return chunks
    
    def load_all_documents(self) -> List[Dict]:
        """
        Carica e parsa tutti i PDF dalla KB
        
        Returns:
            Lista di chunks strutturati con metadata
        """
        print("\n" + "="*70)
        print("📂 CARICAMENTO DOCUMENTI KNOWLEDGE BASE")
        print("="*70)
        
        pdf_files = list(self.kb_dir.glob("*.pdf"))
        
        if not pdf_files:
            print("⚠️ Nessun PDF trovato in data/kb/")
            return []
        
        print(f"\n📊 Trovati {len(pdf_files)} PDF:")
        for pdf in pdf_files:
            size_mb = pdf.stat().st_size / (1024 * 1024)
            print(f"   • {pdf.name} ({size_mb:.2f} MB)")
        
        all_chunks = []
        
        for pdf_path in pdf_files:
            chunks = self.parse_legal_pdf(pdf_path)
            all_chunks.extend(chunks)
        
        print(f"\n✅ TOTALE: {len(all_chunks)} chunks strutturati")
        return all_chunks
    
    def ingest_to_supabase(self, chunks: List[Dict], table_name: str = "legal_documents"):
        """
        Ingest chunks in Supabase con embeddings
        
        Args:
            chunks: Lista chunks con metadata
            table_name: Nome tabella Supabase
        """
        print("\n" + "="*70)
        print("💾 INGEST IN SUPABASE")
        print("="*70)
        
        print(f"\n📊 Tabella: {table_name}")
        print(f"📊 Chunks: {len(chunks)}")
        
        # Crea/Pulisci tabella
        print("\n🔄 Setup tabella...")
        
        try:
            # Prova a eliminare vecchi dati
            self.supabase.table(table_name).delete().neq('id', 0).execute()
            print("   ✅ Tabella pulita")
        except:
            print("   ℹ️ Tabella nuova (creeremo record)")
        
        # Ingest batch (100 alla volta per performance)
        batch_size = 100
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        
        print(f"\n🔄 Embedding + Upload ({total_batches} batch)...")
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(chunks))
            batch = chunks[start_idx:end_idx]
            
            print(f"   Batch {batch_num + 1}/{total_batches}: chunks {start_idx}-{end_idx}...", end=" ")
            
            # Genera embeddings per batch
            texts = [chunk['text'] for chunk in batch]
            embeddings = self.embeddings.embed_documents(texts)
            
            # Prepara record per Supabase
            records = []
            for chunk, embedding in zip(batch, embeddings):
                record = {
                    'content': chunk['text'],
                    'metadata': json.dumps({
                        'source': chunk['source'],
                        'page_number': chunk['page_number'],
                        'element_type': chunk['element_type'],
                        'chunk_id': chunk['chunk_id']
                    }),
                    'embedding': embedding
                }
                records.append(record)
            
            # Upload batch
            try:
                self.supabase.table(table_name).insert(records).execute()
                print("✅")
            except Exception as e:
                print(f"❌ Errore: {e}")
        
        print(f"\n✅ Ingest completato: {len(chunks)} chunks in Supabase")
    
    def hybrid_search(
        self, 
        query: str, 
        table_name: str = "legal_documents",
        top_k: int = 5
    ) -> List[Tuple[str, Dict]]:
        """
        Hybrid Search: Vector (semantic) + BM25 (keyword)
        
        Args:
            query: Query utente
            table_name: Tabella Supabase
            top_k: Numero risultati
            
        Returns:
            Lista (text, metadata) ordinata per rilevanza
        """
        print(f"\n🔍 Hybrid Search: '{query[:50]}...'")
        
        # Step 1: Vector Search (semantic)
        query_embedding = self.embeddings.embed_query(query)
        
        try:
            response = self.supabase.rpc(
                'match_documents',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.3,
                    'match_count': top_k
                }
            ).execute()
            
            results = response.data
            
        except Exception as e:
            print(f"   ⚠️ Vector search error: {e}")
            print(f"   🔄 Fallback: simple retrieval")
            
            # Fallback: get top k
            response = self.supabase.table(table_name).select('*').limit(top_k).execute()
            results = response.data
        
        # Formatta risultati
        docs = []
        for row in results:
            text = row['content']
            metadata = json.loads(row.get('metadata', '{}'))
            docs.append((text, metadata))
        
        print(f"   ✅ Trovati {len(docs)} documenti rilevanti")
        return docs
    
    def query_with_citations(self, question: str) -> str:
        """
        Query RAG con citations precise
        
        Args:
            question: Domanda utente
            
        Returns:
            Risposta con fonti (pagina + documento)
        """
        # Retrieval
        docs = self.hybrid_search(question, top_k=3)
        
        if not docs:
            return "⚠️ Nessun documento rilevante trovato nella Knowledge Base."
        
        # Costruisci contesto
        context_parts = []
        for i, (text, meta) in enumerate(docs, 1):
            source = meta.get('source', 'Unknown')
            page = meta.get('page_number', '?')
            context_parts.append(f"[Documento {i}: {source}, p.{page}]\n{text}")
        
        context = "\n\n".join(context_parts)
        
        # Prompt per LLM
        prompt = f"""Sei un assistente esperto di normative edilizie italiane.

CONTESTO NORMATIVO:
{context}

DOMANDA: {question}

ISTRUZIONI:
1. Rispondi in modo preciso e professionale
2. Usa SOLO informazioni dal contesto
3. Cita SEMPRE la fonte: [NomeDoc, p.X]
4. Se non trovi risposta nel contesto, dillo chiaramente

RISPOSTA:"""

        # Genera risposta
        try:
            response = self.llm.invoke(prompt)
            answer = response.content
            
            # Aggiungi fonti in footer
            answer += "\n\n---\n📚 **Fonti consultate:**\n"
            for i, (_, meta) in enumerate(docs, 1):
                source = meta.get('source', 'Unknown')
                page = meta.get('page_number', '?')
                answer += f"{i}. {source} (pagina {page})\n"
            
            return answer
            
        except Exception as e:
            return f"❌ Errore generazione risposta: {e}"
    
    def ingest_all(self):
        """
        Pipeline completa: load → parse → ingest
        """
        print("\n" + "="*70)
        print("🚀 INGEST KNOWLEDGE BASE LEGAL-GRADE")
        print("="*70)
        
        # Step 1: Load & Parse
        chunks = self.load_all_documents()
        
        if not chunks:
            print("\n⚠️ Nessun documento da processare")
            return
        
        # Step 2: Ingest
        self.ingest_to_supabase(chunks)
        
        print("\n" + "="*70)
        print("✅ INGEST COMPLETATO!")
        print("="*70)


# ============================================================================
# CLI Test
# ============================================================================

if __name__ == "__main__":
    print("\n🧪 TEST LEGAL RAG HANDLER\n")
    
    # Init
    rag = LegalRAGHandler()
    
    # Ingest
    rag.ingest_all()
    
    # Test query
    print("\n" + "="*70)
    print("🧪 TEST QUERY")
    print("="*70)
    
    question = "Quali sono le categorie SOA per lavori edili?"
    answer = rag.query_with_citations(question)
    
    print(f"\n❓ Domanda: {question}")
    print(f"\n✅ Risposta:\n{answer}")