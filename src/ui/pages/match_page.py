"""
Match Bando-Imprese Page
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.parsers.bando_parser import BandoParserUniversale
from core.matching.bando_matcher import BandoMatcher


def render_match_page():
    """Render match bando-imprese page"""
    
    st.title("🎯 Match Bando-Imprese")
    st.markdown("---")
    
    # Info
    with st.expander("ℹ️ Come funziona"):
        st.markdown("""
        ### Processo Automatico
        
        1. **📄 Upload bando PDF** → Il sistema estrae automaticamente:
           - CIG/CUP
           - Importo totale e per categoria
           - Categorie SOA richieste (es. OG1 II, OS30 I)
           - Localizzazione (regione/provincia)
           - Flag PNRR
        
        2. **🔍 Match con database imprese** → Calcola score (0-100):
           - **50 punti:** Categorie SOA compatibili
           - **20 punti:** Opera nella regione
           - **20 punti:** Importo in range capacità
           - **10 punti:** Certificazioni (ISO 9001, etc)
        
        3. **📊 Risultati ordinati** → Top imprese con score ≥ 70% possono partecipare
        
        4. **📧 Alert automatici** → Notifica imprese matchate via email
        
        ### Score Interpretation
        - **≥ 90:** Match perfetto ✅
        - **70-89:** Idonea (potrebbe mancare qualche requisito minore) ⚠️
        - **< 70:** Non idonea ❌
        """)
    
    # Upload bando
    st.markdown("### 📤 Upload Bando")
    
    uploaded_file = st.file_uploader(
        "Carica PDF del bando",
        type=['pdf'],
        help="Formati supportati: PDF testuali, scansioni, layout complessi"
    )
    
    if uploaded_file:
        
        st.success(f"✅ Caricato: {uploaded_file.name}")
        
        # Bottone analisi
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            analyze_btn = st.button(
                "🔍 Analizza e Trova Imprese",
                type="primary",
                use_container_width=True
            )
        
        if analyze_btn:
            
            # Progress
            with st.spinner("📄 Parsing bando..."):
                
                # Salva temporaneamente
                temp_dir = Path("data/temp")
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_path = temp_dir / uploaded_file.name
                
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Parse
                try:
                    parser = BandoParserUniversale()
                    bando = parser.parse(str(temp_path))
                    
                    st.session_state.parsed_bando = bando
                    st.session_state.bando_parsed_success = True
                    
                except Exception as e:
                    st.error(f"❌ Errore parsing: {e}")
                    st.session_state.bando_parsed_success = False
                    return
            
            # Matching
            if st.session_state.bando_parsed_success:
                
                with st.spinner("🔍 Ricerca imprese compatibili..."):
                    
                    try:
                        matcher = BandoMatcher()
                        
                        # Salva bando
                        bando_id = matcher.save_bando(bando)
                        
                        # Match
                        matches = matcher.find_matching_imprese(bando)
                        
                        st.session_state.matches = matches
                        st.session_state.bando_id = bando_id
                        st.session_state.matching_done = True
                        
                    except Exception as e:
                        st.error(f"❌ Errore matching: {e}")
                        st.session_state.matching_done = False
                        return
    
    # Mostra risultati
    if 'matching_done' in st.session_state and st.session_state.matching_done:
        
        bando = st.session_state.parsed_bando
        matches = st.session_state.matches
        
        st.markdown("---")
        st.markdown("## 📊 Risultati Matching")
        
        # Riepilogo bando
        with st.expander("📋 Dettagli Bando", expanded=True):
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("CIG", bando.cig or "N/A")
            
            with col2:
                st.metric("Importo Totale", f"€{bando.importi.totale_appalto:,.0f}")
            
            with col3:
                pnrr_icon = "🇪🇺" if bando.pnrr else "❌"
                st.metric("PNRR", pnrr_icon)
            
            with col4:
                st.metric("Provincia", bando.localizzazione.provincia or "N/A")
            
            # Categorie
            st.markdown("**Categorie Richieste:**")
            categorie_str = ", ".join([
                f"{cat.categoria} {cat.classifica}" + 
                (" [PREVALENTE]" if cat.prevalente else "") +
                (" [SIOS]" if cat.sios else "")
                for cat in bando.categorie
            ])
            st.info(categorie_str)
        
        # Statistiche matching
        st.markdown("### 🎯 Statistiche Matching")
        
        col1, col2, col3, col4 = st.columns(4)
        
        idonee = [m for m in matches if m['can_participate']]
        perfect = [m for m in matches if m['score']['total'] >= 90]
        
        with col1:
            st.metric("🏢 Imprese Totali", len(matches))
        
        with col2:
            st.metric("✅ Idonee", len(idonee))
        
        with col3:
            st.metric("🏆 Match Perfetti", len(perfect))
        
        with col4:
            avg_score = sum(m['score']['total'] for m in matches) / len(matches) if matches else 0
            st.metric("📊 Score Medio", f"{avg_score:.0f}/100")
        
        # Tabella top imprese
        st.markdown("### 🏆 Top 20 Imprese")
        
        # Filtro score minimo
        min_score = st.slider("Score minimo", 0, 100, 70, 5)
        
        filtered_matches = [m for m in matches if m['score']['total'] >= min_score]
        
        if filtered_matches:
            
            # Crea DataFrame
            df_data = []
            for i, match in enumerate(filtered_matches[:20], 1):
                df_data.append({
                    '#': i,
                    'Ragione Sociale': match['ragione_sociale'],
                    'Score': f"{match['score']['total']}/100",
                    'Categorie': f"{match['score']['categorie']}/50",
                    'Regione': f"{match['score']['regione']}/20",
                    'Importo': f"{match['score']['importo']}/20",
                    'Cert.': f"{match['score']['certificazioni']}/10",
                    'Status': '✅ Idonea' if match['can_participate'] else '❌ Non idonea',
                    'Note': ', '.join(match['missing_requirements'][:2]) if match['missing_requirements'] else '-'
                })
            
            df = pd.DataFrame(df_data)
            
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Score': st.column_config.ProgressColumn(
                        'Score',
                        format='%s',
                        min_value=0,
                        max_value=100
                    )
                }
            )
            
            # Export Excel
            st.markdown("---")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                # Excel completo
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Top 20', index=False)
                buffer.seek(0)
                
                st.download_button(
                    label="📊 Scarica Excel (Top 20)",
                    data=buffer,
                    file_name=f"match_bando_{bando.cig}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            with col2:
                # CSV solo idonee
                idonee_df = df[df['Status'] == '✅ Idonea']
                csv = idonee_df.to_csv(index=False).encode('utf-8-sig')
                
                st.download_button(
                    label="📋 Scarica CSV (Solo Idonee)",
                    data=csv,
                    file_name=f"imprese_idonee_{bando.cig}.csv",
                    mime="text/csv"
                )
            
            with col3:
                # Alert via email (TODO)
                st.button(
                    "📧 Invia Alert Imprese",
                    help="Notifica via email le imprese idonee (Coming soon)",
                    disabled=True
                )
        
        else:
            st.warning(f"⚠️ Nessuna impresa trovata con score ≥ {min_score}")
    
    else:
        st.info("👆 Carica un bando per iniziare il matching")


if __name__ == "__main__":
    render_match_page()