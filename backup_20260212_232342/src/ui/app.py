"""
EdilMind - Interfaccia Streamlit
"""
import streamlit as st
import sys
from pathlib import Path
import json
from datetime import datetime

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from config import *
from parser import parse_pdf
from extraction import extract_metadata_completo
from database import insert_bando, get_bandi_attivi, supabase
from semafori import genera_report_semafori

# Config Streamlit
st.set_page_config(
    page_title="EdilMind",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Forza tema scuro


# CSS Custom


# ============================================================================
# HEADER
# ============================================================================
st.title("🏗️ EdilMind - Sistema Matching Intelligente Bandi")
st.markdown("**L'ultimo miglio della digitalizzazione per PMI edili**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurazione")
    
    if not supabase:
        st.error("⚠️ Supabase non configurato!")
        st.info("Modifica il file `.env` con le tue credenziali")
    else:
        st.success("✅ Database connesso")
    
    st.divider()
    
    page = st.radio(
        "Navigazione",
        ["📄 Carica Bando", "🔍 Visualizza Bandi", "👤 Profilo Impresa", "📊 Dashboard"]
    )

# ============================================================================
# PAGINA 1: Carica Bando
# ============================================================================
if page == "📄 Carica Bando":
    st.header("📄 Carica e Analizza Bando")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Carica PDF Disciplinare",
            type=["pdf"],
            help="Carica il disciplinare di gara in formato PDF"
        )
    
    with col2:
        st.info("""
        **Formato supportato:**
        - PDF testuali
        - Disciplinari ANAC
        
        **Cosa viene estratto:**
        - CIG, CPV, Importi
        - Categorie SOA
        - Certificazioni
        - Durata e scadenza
        """)
    
    if uploaded_file:
        # Salva temporaneamente
        temp_path = UPLOADS_DIR / uploaded_file.name
        temp_path.write_bytes(uploaded_file.read())
        
        with st.spinner("🔍 Analisi in corso..."):
            # Parsing
            text = parse_pdf(temp_path)
            
            if not text:
                st.error("❌ Impossibile leggere il PDF")
            else:
                # Estrazione
                metadata = extract_metadata_completo(text)
                
                # Form metadati extra
                st.subheader("📝 Informazioni aggiuntive")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    regione = st.selectbox(
                        "Regione",
                        [""] + sorted(["Liguria", "Toscana", "Piemonte", "Lombardia", 
                                       "Emilia-Romagna", "Veneto", "Lazio", "Campania"])
                    )
                with col_b:
                    scadenza = st.date_input("Scadenza offerte")
                
                if st.button("💾 Salva nel Database", type="primary"):
                    if not metadata.get("cig"):
                        import uuid
                        metadata["cig"] = str(uuid.uuid4())[:10].upper()
                    
                    metadata["regione"] = regione if regione else None
                    metadata["scadenza_offerte"] = scadenza.isoformat() if scadenza else None
                    
                    bando_id = insert_bando(metadata)
                    
                    if bando_id:
                        st.success(f"✅ Bando salvato con ID: {bando_id}")
                        
                        # Mostra riepilogo
                        st.subheader("📊 Riepilogo Estrazione")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("CIG", metadata["cig"])
                            st.metric("Importo Base", f"€{metadata['importi']['base_gara']:,.0f}" if metadata['importi']['base_gara'] else "N/D")
                        
                        with col2:
                            st.metric("CPV Principale", metadata['cpv_codes'][0] if metadata['cpv_codes'] else "N/D")
                            st.metric("Durata", f"{metadata['durata_mesi']} mesi" if metadata['durata_mesi'] else "N/D")
                        
                        with col3:
                            st.metric("Categorie SOA", len(metadata['categorie_soa']))
                            st.metric("Certificazioni", len(metadata['certificazioni_richieste']))
                        
                        # Dettagli
                        with st.expander("🔍 Dettagli Completi"):
                            st.json(metadata)
                    else:
                        st.error("❌ Errore salvataggio")

# ============================================================================
# PAGINA 2: Visualizza Bandi
# ============================================================================
elif page == "🔍 Visualizza Bandi":
    st.header("🔍 Bandi Attivi")
    
    if not supabase:
        st.warning("Configura Supabase per visualizzare i bandi")
    else:
        bandi = get_bandi_attivi(limit=100)
        
        if not bandi:
            st.info("Nessun bando caricato. Vai su 'Carica Bando' per iniziare.")
        else:
            st.success(f"✅ {len(bandi)} bandi trovati")
            
            # Filtri
            col1, col2, col3 = st.columns(3)
            
            with col1:
                regioni = sorted(list(set([b["regione"] for b in bandi if b.get("regione")])))
                filtro_regione = st.multiselect("Regione", regioni)
            
            with col2:
                importo_min = st.number_input("Importo min (€)", value=0, step=50000)
            
            with col3:
                importo_max = st.number_input("Importo max (€)", value=10000000, step=50000)
            
            # Applica filtri
            bandi_filtrati = bandi
            if filtro_regione:
                bandi_filtrati = [b for b in bandi_filtrati if b.get("regione") in filtro_regione]
            
            bandi_filtrati = [b for b in bandi_filtrati 
                             if b.get("importo_base_gara", 0) >= importo_min 
                             and b.get("importo_base_gara", 0) <= importo_max]
            
            st.info(f"🎯 {len(bandi_filtrati)} bandi dopo filtri")
            
            # Mostra bandi
            for bando in bandi_filtrati[:20]:
                with st.expander(f"📋 {bando['cig']} - {(bando.get('titolo') or 'Senza titolo')[:80]}"):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.write(f"**Stazione:** {bando.get('stazione_appaltante', 'N/D')}")
                        st.write(f"**Regione:** {bando.get('regione', 'N/D')}")
                        st.write(f"**Importo:** €{bando.get('importo_base_gara', 0):,.2f}")
                    
                    with col_b:
                        st.write(f"**CPV:** {bando.get('cpv_principale', 'N/D')}")
                        st.write(f"**Durata:** {bando.get('durata_mesi', 'N/D')} mesi")
                        st.write(f"**Scadenza:** {bando.get('scadenza_offerte', 'N/D')}")
                    
                    if bando.get('categorie_soa'):
                        st.write("**Categorie SOA:**")
                        for cat in bando['categorie_soa']:
                            st.write(f"- {cat['codice']} ({cat.get('classe', 'N/D')}): {cat.get('descrizione', '')}")

# ============================================================================
# PAGINA 3: Profilo Impresa
# ============================================================================
elif page == "👤 Profilo Impresa":
    st.header("👤 Gestione Profilo Impresa")
    
    st.info("💡 Configura il profilo della tua impresa per ricevere matching personalizzati")
    
    with st.form("profilo_impresa"):
        ragione_sociale = st.text_input("Ragione Sociale*")
        
        st.subheader("Attestazioni SOA")
        n_soa = st.number_input("Numero attestazioni", min_value=1, max_value=10, value=1)
        
        attestazioni = []
        for i in range(n_soa):
            col1, col2 = st.columns(2)
            with col1:
                cod = st.selectbox(f"Categoria {i+1}", list(CATEGORIE_SOA.keys()), key=f"soa_{i}")
            with col2:
                classe = st.selectbox(f"Classifica {i+1}", list(CLASSI_IMPORTI_MAX.keys()), key=f"classe_{i}")
            
            attestazioni.append({
                "codice": cod,
                "classe": classe,
                "descrizione": CATEGORIE_SOA[cod]
            })
        
        st.subheader("Certificazioni")
        cert_possedute = st.multiselect("Certificazioni possedute", CERTIFICAZIONI_RILEVANTI)
        
        st.subheader("Operatività")
        regioni_op = st.multiselect("Regioni operative", 
                                     ["Liguria", "Toscana", "Piemonte", "Lombardia", 
                                      "Emilia-Romagna", "Veneto", "Lazio"])
        
        col_imp1, col_imp2 = st.columns(2)
        with col_imp1:
            importo_min = st.number_input("Importo minimo interesse (€)", value=50000, step=10000)
        with col_imp2:
            importo_max = st.number_input("Importo massimo capacità (€)", value=1000000, step=100000)
        
        submitted = st.form_submit_button("💾 Salva Profilo", type="primary")
        
        if submitted:
            if not ragione_sociale:
                st.error("Inserisci la ragione sociale")
            else:
                profilo = {
                    "ragione_sociale": ragione_sociale,
                    "attestazioni_soa": attestazioni,
                    "certificazioni_possedute": cert_possedute,
                    "regioni_operative": regioni_op,
                    "importo_min_interesse": importo_min,
                    "importo_max_capacita": importo_max
                }
                
                # Salva in session_state
                st.session_state['profilo_impresa'] = profilo
                st.success("✅ Profilo salvato!")
                
                with st.expander("📄 Anteprima Profilo"):
                    st.json(profilo)

# ============================================================================
# PAGINA 4: Dashboard
# ============================================================================
elif page == "📊 Dashboard":
    st.header("📊 Dashboard Matching")
    
    if 'profilo_impresa' not in st.session_state:
        st.warning("⚠️ Configura prima il profilo impresa nella sezione 'Profilo Impresa'")
    elif not supabase:
        st.warning("⚠️ Configura Supabase per vedere i matching")
    else:
        profilo = st.session_state['profilo_impresa']
        bandi = get_bandi_attivi(limit=50)
        
        if not bandi:
            st.info("Nessun bando disponibile")
        else:
            st.success(f"🔍 Analisi di {len(bandi)} bandi per **{profilo['ragione_sociale']}**")
            
            # Genera report per tutti i bandi
            reports = []
            for bando in bandi:
                report = genera_report_semafori(bando, profilo)
                reports.append(report)
            
            # Filtra per raccomandazione
            verdi = [r for r in reports if "PARTECIPA" in r["raccomandazione"]]
            gialli = [r for r in reports if "VALUTA" in r["raccomandazione"]]
            rossi = [r for r in reports if "NON PARTECIPARE" in r["raccomandazione"]]
            
            # Metriche
            col1, col2, col3 = st.columns(3)
            col1.metric("✅ Consigliati", len(verdi))
            col2.metric("⚡ Da Valutare", len(gialli))
            col3.metric("❌ Sconsigliati", len(rossi))
            
            st.divider()
            
            # Mostra bandi consigliati
            st.subheader("✅ Bandi Consigliati")
            
            for report in verdi[:10]:
                colore_class = "semaforo-verde"
                
                st.markdown(f"""
                <div class="{colore_class}">
                    <h4>{report['cig']} - {report['titolo'][:100]}</h4>
                    <p><strong>Importo:</strong> €{report['importo']:,.0f}</p>
                    <p><strong>Legale:</strong> {report['semaforo_legale']['messaggio']}</p>
                    <p><strong>Economico:</strong> {report['semaforo_economico']['messaggio']}</p>
                    <p><strong>{report['raccomandazione']}</strong></p>
                </div>
                """, unsafe_allow_html=True)

# Footer
st.divider()
st.caption("EdilMind v2.0 - L'ultimo miglio della digitalizzazione | © 2026")
