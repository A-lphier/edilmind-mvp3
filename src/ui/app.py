"""
src/ui/app.py
UI Streamlit Multi-Page EdilMind Enterprise
"""
import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scrapers.anac_scraper import ANACScraper
# from data.province_italia import PROVINCE_ITALIA
from core.rag.rag_handler import LegalRAGHandler
from core.chat.llm_handler import LLMHandler, chat_with_rag
import os

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="EdilMind Enterprise",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# INIT SESSION STATE
# ============================================================================

if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = LegalRAGHandler(kb_dir="data/kb")

if "scraper" not in st.session_state:
    st.session_state.scraper = ANACScraper()
    st.session_state.bandi_cache = {}

if "llm_handler" not in st.session_state:
    from dotenv import load_dotenv
    load_dotenv(override=True)

    groq_key = os.getenv("GROQ_API_KEY")
    print(f"🔍 DEBUG: GROQ_API_KEY trovata (primi 10 char): {groq_key[:10] if groq_key else 'NESSUNA'}")

    forced_model = "llama-3.1-8b-instant"
    print(f"🔧 FORCED MODEL: {forced_model}")

    st.session_state.llm_handler = LLMHandler()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.title("🏗️ EdilMind Enterprise")
    st.markdown("---")
    
    # Geolocalizzazione
    st.subheader("🔍 Geolocalizzazione")
    
    st.markdown("**Provincia/Area Bando**")
    
    # Lista province
    province_options = [
        "Bergamo (BG) - Lombardia",
        "Milano (MI) - Lombardia", 
        "Roma (RM) - Lazio",
        "Napoli (NA) - Campania",
        "Torino (TO) - Piemonte"
    ]
    
    selected_label = st.selectbox(
        "Provincia",
        province_options,
        index=0,
        label_visibility="collapsed"
    )
    
    # Parse provincia selezionata
    nome = selected_label.split('(')[0].strip()
    sigla = selected_label.split('(')[1].split(')')[0]
    regione = selected_label.split(' - ')[1]
    
    selected_prov = {
        'nome': nome,
        'sigla': sigla,
        'regione': regione,
        'lat': 45.6983,
        'lon': 9.6773
    }
    
    if selected_prov:
        st.success(f"✅ {selected_label}")
        st.info(f"**Regione:** {selected_prov['regione']}")
        st.info(f"**Coordinate:** {selected_prov['lat']:.4f}, {selected_prov['lon']:.4f}")

    st.markdown("---")
    
    # RAG Stats
    st.subheader("📚 Knowledge Base")
    
    st.markdown("""
    **Sistema RAG Attivo:**
    - 📄 **Documenti:** 3 PDF normativi
    - 💾 **Vector Store:** Supabase (88 chunks)
    - 🔍 **Embeddings:** Sentence Transformers
    - 🤖 **LLM:** Groq Llama 3.1 70B
    - ✅ **Citations:** Automatiche
    """)

    st.markdown("---")
    
    # Navigation
    st.subheader("📂 Navigazione")
    
    page = st.radio(
        "Vai a:",
        ["Chat Assistente", "Parser SOA", "Batch Parser", "Match Bando-SOA", "Mappa Bandi"],
        label_visibility="collapsed"
    )

# ============================================================================
# MAIN CONTENT
# ============================================================================

if page == "Chat Assistente":
    st.title("💬 Chat con Assistente AI")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])
                    
                    # Show sources if available
                    if "sources" in msg and msg["sources"]:
                        with st.expander("📎 Fonti utilizzate"):
                            for src in msg["sources"]:
                                st.markdown(f"- {src.get('source', 'N/A')}")
    
    # Chat input
    user_input = st.chat_input("Fai una domanda sui bandi o normative...")
    
    if user_input:
        # Add user message
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Get response with RAG
        with st.chat_message("assistant"):
            with st.spinner("🔍 Analisi in corso..."):
                try:
                    answer, sources = chat_with_rag(
                        user_input,
                        st.session_state.chat_history,
                        rag_engine=st.session_state.rag_engine,
                        llm_handler=st.session_state.llm_handler
                    )
                    
                    st.markdown(answer)
                    
                    # Show sources
                    if sources:
                        with st.expander("📎 Fonti utilizzate"):
                            for src in sources:
                                st.markdown(f"- {src.get('source', 'N/A')}")
                    
                    # Add to history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                    
                except Exception as e:
                    st.error(f"❌ Errore: {e}")

elif page == "Parser SOA":
    from pages.soa_parser_page import render_soa_parser
    render_soa_parser()

elif page == "Batch Parser":
    from pages.batch_parser_page import render_batch_parser
    render_batch_parser()

elif page == "Match Bando-SOA":
    from pages.match_page import render_match_page
    render_match_page()

elif page == "Mappa Bandi":
    from pages.mappa_bandi_page import render_mappa_bandi
    render_mappa_bandi()