"""
src/core/chat/llm_handler.py
Handler LLM per chat con RAG context
"""
import os
import logging
from typing import List, Dict, Optional
from groq import Groq
from openai import OpenAI
from dotenv import load_dotenv

# Force load .env
load_dotenv(override=True)

logger = logging.getLogger(__name__)

class LLMHandler:
    """
    Handler unificato per LLM (Groq/OpenAI) con supporto RAG.
    """
    
    def __init__(
        self,
        provider: str = "groq",
        groq_api_key: str = None,
        openai_api_key: str = None
    ):
        self.provider = provider

        if provider == "groq":
            # Carica da env se non passato
            if not groq_api_key:
                groq_api_key = os.getenv("GROQ_API_KEY")
            
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY richiesta (manca in .env)")
            
            self.client = Groq(api_key=groq_api_key)
            self.model = "llama-3.1-70b-versatile"
            
        elif provider == "openai":
            if not openai_api_key:
                openai_api_key = os.getenv("OPENAI_API_KEY")
            
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY richiesta (manca in .env)")
            
            self.client = OpenAI(api_key=openai_api_key)
            self.model = "gpt-4-turbo-preview"
        else:
            raise ValueError(f"Provider non supportato: {provider}")

        print(f"✅ LLM Handler inizializzato con successo")

    def chat(
        self,
        messages: List[Dict],
        rag_context: str = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        stream: bool = False
    ):
        """
        Chat con LLM + RAG context opzionale
        """
        # Prepara messaggi
        if rag_context:
            # Inserisci contesto RAG come system message
            system_msg = {
                "role": "system",
                "content": f"Contesto normativo:\n{rag_context}\n\nRispondi in modo professionale usando il contesto fornito."
            }
            full_messages = [system_msg] + messages
        else:
            full_messages = messages

        # Call LLM
        if self.provider == "groq":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
        elif self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
        
        return response


def chat_with_rag(
    user_message: str,
    chat_history: List[Dict],
    rag_engine,
    llm_handler: LLMHandler
) -> tuple[str, List[Dict]]:
    """
    Chat con Legal RAG (Supabase + Citations).

    Args:
        user_message: Messaggio utente corrente
        chat_history: Storia chat precedente
        rag_engine: Istanza LegalRAGHandler
        llm_handler: Istanza LLMHandler

    Returns:
        (risposta_assistant, fonti_rag)
    """
    # 1. Query Legal RAG con citations
    try:
        answer = rag_engine.query_with_citations(user_message)
        
        # Estrai fonti dal footer (se presenti)
        sources = []
        if "📚 **Fonti consultate:**" in answer:
            answer_parts = answer.split("📚 **Fonti consultate:**")
            answer = answer_parts[0].strip()
            sources_text = answer_parts[1].strip()
            
            # Parse fonti
            for line in sources_text.split('\n'):
                if line.strip():
                    sources.append({
                        'source': line.strip(),
                        'category': 'legal_kb'
                    })
        
        return answer, sources
        
    except Exception as e:
        print(f"❌ Errore RAG: {e}")
        # Fallback: risposta senza RAG
        return f"⚠️ Errore nel recupero documenti: {e}", []