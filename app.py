import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# Initialisation ultra-sécurisée
if 'events' not in st.session_state:
    st.session_state.events = []
if 'apps' not in st.session_state:
    st.session_state.apps = []

# --- 2. BARRE LATÉRALE ---
with st.sidebar:
    st.title("⚙️ Administration")
    
    # AJOUT D'APP : Utilisation d'un formulaire dédié pour isoler l'action
    st.subheader("🚀 Applications")
    with st.form("form_new_app", clear_on_submit=True):
        new_app_name = st.text_input("Nom de l'appli").upper().strip()
        add_btn = st.form_submit_button("Ajouter")
        if add_btn and new_app_name:
            if new_app_name not in st.session_state.apps:
                st.session_state.apps.append(new_app_name)
                st.rerun()
            else:
                st.warning("Existe déjà")

    st.divider()
    
    # AJOUT D'ÉVÉNEMENT
    st.subheader("➕ Nouvel Événement")
    # Liste de choix sécurisée
    current_options = sorted(st.session_state.apps)
    
    with st.form("form_event", clear_on_submit=True):
        f_app = st.selectbox("Application", options=current_options if current_options else ["Veuillez ajouter une app"])
        f_env = st.selectbox("Environnement", ["PROD", "PRÉPROD", "RECETTE"])
        f_type = st.selectbox("Type", ["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"])
        f_comment = st.text_area("Commentaire")
        col1, col2 = st.columns(2)
        f_d1 = col1.date_input("Début")
        f_d2 = col2.date_input("Fin")
        
        if st.form_submit_button("Enregistrer"):
            if current_options:
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
            st.info("💡 Le planning est vide. Ajoutez une application dans la barre latérale pour commencer.")
        else:
            # On trie les apps pour l'affichage
            apps_list = sorted(st.session_state.apps)
            
            # Préparation des données de la grille
            grid = {"App": apps_list}
            for d in dates:
                col = str(d.day)
                grid[col] = []
                for app in apps_list:
                    status = ""
                    if d.weekday() >= 5: status = "•" # Marqueur Weekend
                    
                    # Recherche d'un événement
                    for ev in st.session_state.events:
                        if ev['app'] == app and ev['env'] == env_selected:
                            if ev['d1'] <= d <= ev['d2']:
                                status = ev['type'][:3] # MEP, INC...
                    grid[col].append(status)
            
            df_display = pd.DataFrame(grid)

            # Style des colonnes
            c_config = {"App": st.column_config.TextColumn("Application", width="medium", pinned=True)}
            for d in dates:
                c_config[str(d.day)] = st.column_config.TextColumn(str(d.day), width=35)

            # Style des couleurs
            def apply_style(val):
                colors = {
                    "MEP": "background-color: #0070C0; color: white; font-weight: bold",
                    "INC": "background-color: #FF0000; color: white; font-weight: bold",
                    "MAI": "background-color: #FFC000; color: black; font-weight: bold",
                    "TES": "background-color: #00B050; color: white; font-weight: bold",
                    "MOR": "background-color: #9600C8; color: white; font-weight: bold",
                    "•": "background-color: #f1f3f4; color: transparent"
                }
                return colors.get(val, "")

            # AFFICHAGE DU TABLEAU
            sel = st.dataframe(
                df_display.style.map(apply_style),
                use_container_width=True,
                hide_index=True,
                column_config=c_config,
                on_select="rerun",
                selection_mode=["single_row", "single_column"]
            )

            # --- 4. LOGIQUE DE CLIC SUR CELLULE ---
            s_rows = sel.selection.rows
            s_cols = sel.selection.columns

            if s_rows and s_cols:
                row_idx = s_rows[0]
                col_name = s_cols[0]

                if col_name != "App":
                    selected_app = apps_list[row_idx]
                    day_num = int(col_name)
                    clicked_date = date(year, month_num,
