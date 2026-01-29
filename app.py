import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# Initialisation des variables en mémoire
if 'events' not in st.session_state: st.session_state.events = []
if 'apps' not in st.session_state: st.session_state.apps = []

# --- 2. BARRE LATÉRALE ---
with st.sidebar:
    st.title("⚙️ Administration")
    with st.expander("🚀 Gérer les Applications"):
        new_app = st.text_input("Nom de l'appli").upper()
        if st.button("Ajouter"):
            if new_app and new_app not in st.session_state.apps:
                st.session_state.apps.append(new_app)
                st.rerun()
        
    st.divider()
    st.subheader("➕ Nouvel Événement")
    with st.form("add_event", clear_on_submit=True):
        f_app = st.selectbox("Application", sorted(st.session_state.apps) if st.session_state.apps else [""])
        f_env = st.selectbox("Environnement", ["PROD", "PRÉPROD", "RECETTE"])
        f_type = st.selectbox("Type", ["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"])
        f_comment = st.text_area("Commentaire / Détails")
        col1, col2 = st.columns(2)
        f_d1 = col1.date_input("Début")
        f_d2 = col2.date_input("Fin")
        if st.form_submit_button("Enregistrer"):
            if f_app:
                st.session_state.events.append({
                    'app': f_app, 'env': f_env, 'type': f_type, 
                    'd1': f_d1, 'd2': f_d2, 'comment': f_comment
                })
                st.success("Enregistré !")
                st.rerun()

# --- 3. INTERFACE PRINCIPALE ---
st.title("📅 Planning IT - 2026")
env_selected = st.radio("Secteur :", ["PROD", "PRÉPROD", "RECETTE"], horizontal=True)

mois_noms = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
tabs = st.tabs(mois_noms)

for i, tab in enumerate(tabs):
    with tab:
        month_num = i + 1
        year = 2026
        num_days = calendar.monthrange(year, month_num)[1]
        dates = [date(year, month_num, d) for d in range(1, num_days + 1)]
        
        if not st.session_state.apps:
            st.info("Ajoutez une application dans le menu à gauche.")
        else:
            apps = sorted(st.session_state.apps)
            grid_data = {"App": apps}
            for d in dates:
                col_name = str(d.day)
                grid_data[col_name] = []
                for app in apps:
                    val = ""
                    if d.weekday() >= 5: val = "•"
                    for ev in st.session_state.events:
                        if ev['app'] == app and ev['env'] == env_selected:
                            if ev['d1'] <= d <= ev['d2']:
                                val = ev['type'][:3]
                    grid_data[col_name].append(val)
            
            df = pd.DataFrame(grid_data)

            # Configuration des colonnes
            config_cols = {"App": st.column_config.TextColumn("Application", width="medium", pinned=True)}
            for d in dates:
                config_cols[str(d.day)] = st.column_config.TextColumn(str(d.day), width=35)

            # Style des couleurs (utilisation de .map pour Pandas 2.0+)
            def color_excel(val):
                if val == "MEP": return "background-color: #0070C0; color: white; font-weight: bold"
                if val == "INC": return "background-color: #FF0000; color: white; font-weight: bold"
                if val == "MAI": return "background-color: #FFC000; color: black; font-weight: bold"
                if val == "TES": return "background-color: #00B050; color: white; font-weight: bold"
                if val == "MOR": return "background-color: #9600C8; color: white; font-weight: bold"
                if val == "•": return "background-color: #f1f3f4; color: transparent"
                return ""

            # --- AFFICHAGE ET SÉLECTION ---
            # Correction de la syntaxe de sélection pour Streamlit 1.53+
            event = st.dataframe(
                df.style.map(color_excel),
                use_container_width=True,
                hide_index=True,
                column_config=config_cols,
                on_select="rerun",
                selection_mode=["single_row", "single_column"]
            )

            # --- 4. RÉCUPÉRATION DU CLIC ---
            # On vérifie si une ligne ET une colonne sont sélectionnées
            sel_rows = event.selection.rows
            sel_cols = event.selection.columns

            if sel_rows and sel_cols:
                row_idx
