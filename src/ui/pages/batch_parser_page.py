"""
Batch Parser Bandi - Upload e analisi multipla bandi
"""
import streamlit as st
import sys
import os
from pathlib import Path
import json
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.parsers.bando_parser import BandoParserUniversale


def render_batch_parser():
    """Render batch parser bandi page"""
    
    st.title("📋 Analisi Batch Bandi")
    st.markdown("---")
    
    # Info
    with st.expander("ℹ️ Come funziona l'analisi batch"):
        st.markdown("""
        ### Funzionalità
        
        Carica **uno o più PDF di bandi** contemporaneamente e il sistema estrae automaticamente:
        
        - 🔢 **CIG/CUP** e codici identificativi
        - 💰 **Importi** (totale, lavori, sicurezza, manodopera)
        - 📂 **Categorie SOA** richieste (OG1, OS30, etc.)
        - 📊 **Classifiche** necessarie (I-VIII)
        - 🏗️ **Requisiti speciali** (SIOS, avvalimento, subappalto)
        - 🇪🇺 **Flag PNRR** (finanziamento EU)
        - 📍 **Localizzazione** (regione, provincia)
        - 📋 **Tipo procedura** e criterio aggiudicazione
        
        ### Formati supportati
        
        ✅ PDF testuali (ANAC, SUA, SINTEL, etc.)  
        ✅ PDF scansionati (con OCR automatico)  
        ✅ Layout complessi (multi-colonna, tabelle)  
        
        ### Output
        
        - Tabella riepilogativa con tutti i bandi analizzati
        - Export Excel/JSON per analisi offline
        - Salvataggio automatico nel database bandi
        """)
    
    # Upload multiplo
    st.markdown("### 📤 Upload Bandi (max 20 file)")
    
    uploaded_files = st.file_uploader(
        "Carica uno o più PDF di bandi",
        type=['pdf'],
        accept_multiple_files=True,
        help="Puoi selezionare fino a 20 PDF contemporaneamente"
    )
    
    if uploaded_files:
        
        st.success(f"✅ Caricati {len(uploaded_files)} file")
        
        # Mostra lista file
        with st.expander(f"📁 File caricati ({len(uploaded_files)})"):
            for i, f in enumerate(uploaded_files, 1):
                size_mb = f.size / 1024 / 1024
                st.write(f"{i}. **{f.name}** - {size_mb:.2f} MB")
        
        st.markdown("---")
        
        # Bottone analisi
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            analyze_btn = st.button(
                f"🔍 Analizza {len(uploaded_files)} Bandi",
                type="primary",
                use_container_width=True
            )
        
        if analyze_btn:
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Salva temporaneamente
            temp_dir = Path("data/temp/bandi_batch")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize parser
            if 'bando_parser' not in st.session_state:
                st.session_state.bando_parser = BandoParserUniversale()
            
            parser = st.session_state.bando_parser
            
            # Parse tutti i file
            risultati = []
            errori = []
            
            for i, uploaded_file in enumerate(uploaded_files):
                
                # Update progress
                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                status_text.text(f"📄 Analisi {i+1}/{len(uploaded_files)}: {uploaded_file.name}")
                
                # Salva file
                temp_path = temp_dir / uploaded_file.name
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Parse
                try:
                    bando = parser.parse(str(temp_path))
                    
                    # Converti in dict per tabella
                    risultati.append({
                        'file': uploaded_file.name,
                        'cig': bando.cig or 'N/A',
                        'pnrr': '🇪🇺 Sì' if bando.pnrr else 'No',
                        'importo_totale': f"€ {bando.importi.totale_appalto:,.2f}",
                        'importo_lavori': f"€ {bando.importi.lavori:,.2f}" if bando.importi.lavori else 'N/A',
                        'categorie': ', '.join([f"{c.categoria} {c.classifica}" for c in bando.categorie]),
                        'provincia': bando.localizzazione.provincia or 'N/A',
                        'criterio': bando.procedura.criterio,
                        'confidence': bando.confidence_score,
                        'bando_obj': bando  # Oggetto completo
                    })
                    
                except Exception as e:
                    errori.append({
                        'file': uploaded_file.name,
                        'errore': str(e)
                    })
            
            progress_bar.empty()
            status_text.empty()
            
            # Store results
            st.session_state.batch_risultati = risultati
            st.session_state.batch_errori = errori
            
            # Summary
            st.success(f"✅ Analisi completata: {len(risultati)} successi, {len(errori)} errori")
        
        # Mostra risultati
        if 'batch_risultati' in st.session_state:
            
            risultati = st.session_state.batch_risultati
            errori = st.session_state.batch_errori
            
            st.markdown("---")
            st.markdown("## 📊 Risultati Analisi")
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📋 Bandi Analizzati", len(risultati))
            
            with col2:
                pnrr_count = sum(1 for r in risultati if '🇪🇺' in r['pnrr'])
                st.metric("🇪🇺 PNRR", pnrr_count)
            
            with col3:
                if risultati:
                    importi = [float(r['importo_totale'].replace('€ ', '').replace(',', '')) for r in risultati if 'N/A' not in r['importo_totale']]
                    importo_tot = sum(importi) / 1000000 if importi else 0
                    st.metric("💰 Importo Totale", f"€ {importo_tot:.1f}M")
                else:
                    st.metric("💰 Importo Totale", "€ 0")
            
            with col4:
                if errori:
                    st.metric("❌ Errori", len(errori), delta=f"-{len(errori)}", delta_color="inverse")
                else:
                    st.metric("✅ Successi", len(risultati))
            
            # Tabella risultati
            if risultati:
                st.markdown("### 📋 Bandi Estratti")
                
                df = pd.DataFrame(risultati)
                df_display = df.drop(columns=['bando_obj'])  # Rimuovi oggetto completo
                
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Download Excel
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Excel
                    from io import BytesIO
                    buffer = BytesIO()
                    df_display.to_excel(buffer, index=False, engine='openpyxl')
                    buffer.seek(0)
                    
                    st.download_button(
                        label="📊 Scarica Excel",
                        data=buffer,
                        file_name=f"bandi_analisi_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                with col2:
                    # JSON completo
                    json_data = json.dumps(
                        [r['bando_obj'].dict() for r in risultati],
                        indent=2,
                        ensure_ascii=False,
                        default=str
                    )
                    
                    st.download_button(
                        label="💾 Scarica JSON",
                        data=json_data,
                        file_name=f"bandi_completi_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json"
                    )
            
            # Errori
            if errori:
                st.markdown("---")
                st.markdown("### ❌ Errori Rilevati")
                
                for err in errori:
                    st.error(f"**{err['file']}**: {err['errore']}")
    
    else:
        st.info("👆 Carica uno o più PDF di bandi per iniziare l'analisi batch")


if __name__ == "__main__":
    render_batch_parser()