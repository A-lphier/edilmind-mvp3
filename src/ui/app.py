import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Aggiungi src/ al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scrapers.anac_scraper import ANACScraper
# from data.province_italia import PROVINCE_ITALIA
# from core.rag.rag_handler import LegalRAGHandler
# from core.chat.llm_handler import LLMHandler, chat_with_rag
import os

# ====================================================================
# CONFIG PAGINA
# ====================================================================
st.set_page_config(
    page_title="EdilMind - Scraper Gare ANAC",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================================================================
# SESSION STATE
# ====================================================================

# RAG disabilitato per Streamlit Cloud
# if "rag_engine" not in st.session_state:
#     st.session_state.rag_engine = LegalRAGHandler(kb_dir="data/kb")

if "scraper" not in st.session_state:
    st.session_state.scraper = ANACScraper()

# LLM handler disabilitato per Streamlit Cloud
# if "llm_handler" not in st.session_state:
#     from dotenv import load_dotenv
#     load_dotenv(override=True)
#     groq_key = os.getenv("GROQ_API_KEY")
#     if not groq_key:
#         st.error("GROQ_API_KEY mancante!")
#     else:
#         st.session_state.llm_handler = LLMHandler()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ====================================================================
# SIDEBAR
# ====================================================================
with st.sidebar:
    st.title("🏗️ EdilMind")
    st.caption("SaaS B2B per Matching Gare Edili")
    
    # Menu navigazione
    page = st.radio(
        "Navigazione",
        ["🏠 Home", "📡 Scraper ANAC", "📄 Upload SOA", "💬 Chat Normativa"],
        label_visibility="collapsed"
    )

# ====================================================================
# HOME PAGE
# ====================================================================
if "Home" in page:
    st.title("🏗️ EdilMind - MVP Dashboard")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Bandi Caricati", len(st.session_state.get("bandi_df", pd.DataFrame())))
    with col2:
        st.metric("SOA Attive", 0)
    with col3:
        st.metric("Match Trovati", 0)
    
    st.divider()
    
    st.subheader("🚀 Quick Start")
    st.info("""
    **Versione MVP (Streamlit Cloud):**
    - ✅ Scraper ANAC funzionante
    - ✅ Upload SOA PDF
    - ⚠️ Chat RAG temporaneamente disabilitata (deploy in corso su Render.com)
    
    **Inizia da:** Scraper ANAC → carica bandi pubblici
    """)

# ====================================================================
# SCRAPER ANAC PAGE
# ====================================================================
elif "Scraper" in page:
    st.title("📡 Scraper Gare ANAC")
    
    with st.form("scraper_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            keywords = st.text_input("Parole chiave", "edilizia lavori pubblici")
        
        with col2:
            max_results = st.number_input("Max risultati", 10, 50, 20)
        
        submit = st.form_submit_button("🔍 Cerca Bandi", use_container_width=True)
    
    if submit:
        with st.spinner("Ricerca in corso..."):
            bandi = st.session_state.scraper.scrape_bandi(keywords, max_results)
            st.session_state.bandi_df = pd.DataFrame(bandi)
            st.success(f"✅ Trovati {len(bandi)} bandi!")
    
    if "bandi_df" in st.session_state and not st.session_state.bandi_df.empty:
        st.dataframe(st.session_state.bandi_df, use_container_width=True)

# ====================================================================
# UPLOAD SOA PAGE
# ====================================================================
elif "Upload SOA" in page:
    st.title("📄 Upload Attestazione SOA")
    
    uploaded = st.file_uploader("Carica PDF SOA", type=["pdf"])
    
    if uploaded:
        st.success(f"✅ File caricato: {uploaded.name}")
        st.info("Parser SOA in sviluppo...")

# ====================================================================
# CHAT PAGE
# ====================================================================
elif "Chat" in page:
    st.title("💬 Chat Normativa Appalti")
    
    st.warning("⚠️ Sistema RAG temporaneamente disabilitato. Deploy in corso su Render.com per supporto completo.")
    
    st.info("""
    **Funzionalità previste:**
    - Query semantica su Codice Appalti
    - Analisi CAM (Criteri Ambientali Minimi)
    - Guardrails requisiti SOA
    """)
