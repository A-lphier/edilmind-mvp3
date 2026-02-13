"""
LLM Handler - Gestione provider LLM multipli
"""
import os
from typing import Optional, Dict, Any, List
from groq import Groq

class LLMHandler:
    """
    Handler unificato per provider LLM
    Supporta: Groq, Ollama, OpenAI
    """
    
    def __init__(self, provider: str = "groq", groq_api_key: Optional[str] = None):
        """
        Inizializza LLM Handler
        
        Args:
            provider: Provider da usare (groq, ollama, openai)
            groq_api_key: API key per Groq
        """
        self.provider = provider.lower()
        
        if self.provider == "groq":
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY obbligatoria per provider Groq")
            
            self.client = Groq(api_key=groq_api_key)
            self.model = "llama-3.1-8b-instant"  # Modello attivo
            
            print(f"✅ LLM Handler: Groq ({self.model})")
        
        else:
            raise ValueError(f"Provider '{provider}' non supportato")
    
    def generate(self, 
                 prompt: str, 
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.3,
                 max_tokens: int = 1000) -> str:
        """
        Genera risposta da LLM
        
        Args:
            prompt: Prompt utente
            system_prompt: System prompt (opzionale)
            temperature: Creatività (0-1)
            max_tokens: Lunghezza massima risposta
        
        Returns:
            Risposta generata
        """
        if self.provider == "groq":
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Errore Groq: {error_msg}")
                
                # Suggerimenti se modello deprecato
                if "decommissioned" in error_msg.lower():
                    print("💡 Modello deprecato. Modelli Groq attivi:")
                    print("   - mixtral-8x7b-32768 (consigliato)")
                    print("   - mixtral-8x7b-32768")
                    print("   - gemma2-9b-it")
                
                raise
        
        return ""
    
    def chat(self, 
             messages: List[Dict[str, str]], 
             temperature: float = 0.3,
             max_tokens: int = 1000) -> str:
        """
        Chat multi-turno
        
        Args:
            messages: Lista messaggi formato OpenAI
            temperature: Creatività
            max_tokens: Lunghezza max
        
        Returns:
            Risposta
        """
        if self.provider == "groq":
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                print(f"❌ Errore chat Groq: {e}")
                raise
        
        return ""

# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    import sys
    
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("❌ GROQ_API_KEY non configurata")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("🧪 TEST LLM HANDLER")
    print("="*60 + "\n")
    
    # Init
    llm = LLMHandler(provider="groq", groq_api_key=api_key)
    
    # Test semplice
    response = llm.generate(
        prompt="Cos'è un decreto legislativo? Rispondi in 50 parole.",
        system_prompt="Sei un assistente esperto in diritto italiano.",
        temperature=0.3,
        max_tokens=200
    )
    
    print("📝 Risposta LLM:")
    print("-" * 60)
    print(response)
    print("-" * 60)
    
    print("\n✅ Test completato")