"""
SOA Parser Page - Upload e analisi Attestazioni SOA
"""
import streamlit as st
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.parsers.soa_parser import SOAParser

def render_soa_parser():
    """Render SOA Parser page"""
    
    st.title("📜 Parser Attestazione SOA")
    st.markdown("---")
    
    # Info box
    with st.expander("ℹ️ Come funziona"):
        st.markdown("""
        ### Cosa fa il Parser SOA?
        
        Carica un PDF della tua **Attestazione SOA** e il sistema estrae automaticamente:
        
        - 🏢 **Ragione Sociale** dell'impresa
        - 🔢 **Partita IVA**
        - 📂 **Categorie qualificate** (es. OG1, OG3, OS6)
        - 📊 **Classifiche** per categoria (I, II, III, IV, V, VI, VII, VIII)
        - 📅 **Data scadenza** attestazione
        - 🏛️ **Organismo SOA** emittente
        
        ### Perché è utile?
        
        ✅ **Velocità**: Niente più inserimento manuale  
        ✅ **Precisione**: Riduce errori di trascrizione  
        ✅ **Matching**: Base per il semaforo legale bandi  
        
        ### Formati supportati
        
        - PDF Attestazioni SOA standard italiani
        - Tutti gli organismi SOA certificati
        """)
    
    # Upload section
    st.markdown("### 📤 Upload Attestazione SOA")
    
    uploaded_file = st.file_uploader(
        "Carica PDF Attestazione SOA",
        type=['pdf'],
        help="Formato: PDF. Max 10MB"
    )
    
    if uploaded_file:
        # Mostra info file
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 Nome File", uploaded_file.name)
        with col2:
            size_mb = uploaded_file.size / 1024 / 1024
            st.metric("💾 Dimensione", f"{size_mb:.2f} MB")
        with col3:
            st.metric("📋 Tipo", uploaded_file.type)
        
        # Salva temporaneamente
        temp_dir = Path("data/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        temp_path = temp_dir / uploaded_file.name
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Parse button
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🔍 Analizza Attestazione", type="primary", use_container_width=True):
                
                with st.spinner("⚙️ Parsing in corso..."):
                    # Initialize parser
                    if 'soa_parser' not in st.session_state:
                        st.session_state.soa_parser = SOAParser()
                    
                    parser = st.session_state.soa_parser
                    
                    # Parse
                    result = parser.parse(str(temp_path))
                    
                    # Store in session
                    st.session_state.soa_data = result
                
                # Mostra risultati
                if result.get('success'):
                    st.success("✅ Parsing completato con successo!")
                else:
                    st.error(f"❌ Errore: {result.get('error', 'Parsing fallito')}")
        
        # Mostra risultati se disponibili
        if 'soa_data' in st.session_state and st.session_state.soa_data.get('success'):
            data = st.session_state.soa_data
            
            st.markdown("---")
            st.markdown("## 📊 Dati Estratti")
            
            # Dati principali
            col1, col2 = st.columns(2)
            
            with col1:
                if 'ragione_sociale' in data:
                    st.markdown("### 🏢 Ragione Sociale")
                    st.info(data['ragione_sociale'])
                
                if 'partita_iva' in data:
                    st.markdown("### 🔢 Partita IVA")
                    st.info(data['partita_iva'])
            
            with col2:
                if 'scadenza' in data:
                    st.markdown("### 📅 Scadenza")
                    st.warning(data['scadenza'])
                
                if 'organismo_soa' in data:
                    st.markdown("### 🏛️ Organismo SOA")
                    st.info(data['organismo_soa'])
            
            # Categorie
            if data.get('categorie'):
                st.markdown("### 📂 Categorie Qualificate")
                
                st.markdown(f"**Totale categorie:** {len(data['categorie'])}")
                
                # Tabella categorie
                import pandas as pd
                
                df = pd.DataFrame(data['categorie'])
                df.columns = ['Categoria', 'Classifica']
                
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Download risultati
                st.markdown("---")
                
                import json
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                
                st.download_button(
                    label="💾 Scarica Dati (JSON)",
                    data=json_str,
                    file_name=f"soa_parsed_{data.get('file_name', 'data')}.json",
                    mime="application/json"
                )
            
            # Alert se scadenza vicina
            if 'scadenza' in data:
                from datetime import datetime
                try:
                    # Parse data (supporta vari formati)
                    scad_str = data['scadenza'].replace('/', '-')
                    scad_date = datetime.strptime(scad_str, '%d-%m-%Y')
                    
                    days_left = (scad_date - datetime.now()).days
                    
                    if days_left < 90:
                        st.error(f"⚠️ ATTENZIONE: Attestazione in scadenza tra {days_left} giorni!")
                    elif days_left < 180:
                        st.warning(f"⏰ Attestazione in scadenza tra {days_left} giorni")
                except:
                    pass
    
    else:
        # Placeholder quando nessun file
        st.info("👆 Carica un PDF di Attestazione SOA per iniziare l'analisi")
        
        # Esempio screenshot (opzionale)
        st.markdown("### 📸 Esempio Attestazione SOA")
        st.markdown("""
        Il parser è compatibile con attestazioni di tutti gli organismi SOA certificati:
        - SOA Nazionale
        - Cqop SOA
        - Bureau Veritas
        - Cooprogetti SOA
        - Etc.
        """)

if __name__ == "__main__":
    render_soa_parser()