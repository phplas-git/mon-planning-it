import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta

# --- 1. CONFIGURATION (DOIT ÊTRE LA PREMIÈRE LIGNE) ---
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# Initialisation sécurisée du Session State
for key in ['events', 'apps']:
    if key not in st.session_state:
        st.session_state[key] = []

# --- 2. BARRE LATÉRALE ---
with st.sidebar:
    st.title("⚙️ Administration")
    
    # Gestion des Apps
    st.subheader("🚀 Applications")
    new_app = st.text_input("Nom de l'appli", key="txt_app").upper().strip()
    if st.button("Ajouter l'App"):
        if new_app and new_app not in st.session_state.apps:
            st.session_state.apps.append(new_app)
            st.rerun()

    st.divider()
    
    # Gestion des Événements
    st.subheader("➕ Nouvel Événement")
    if not st.session_state.apps:
        st.warning("Ajoutez une application d'abord.")
    else:
        with st.form("form_event", clear_on_submit=True):
            f_app = st.selectbox("Application", sorted(st.session_state.apps))
            f_env = st.selectbox("Environnement", ["PROD", "PRÉPROD", "RECETTE"])
            f_type = st.selectbox("Type", ["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"])
            f_comment = st.text_area("Commentaire")
            c1, c2 = st.columns(2)
            f_d1 = c1.date_input("Début")
            f_d2 = c2.date_input("Fin")
            
            if st.form_submit_button("Enregistrer"):
                st.session_state.events.append({
                    'app': f_app, 'env': f_env, 'type': f_type, 
                    'd1': f_d1, 'd2': f_d2, 'comment': f_comment
                })
                st.success("Enregistré !")
                st.rerun()

    if st.button("🗑️ Tout effacer"):
        st.session_state.apps = []
        st.session_state.events = []
        st.rerun()

# --- 3. INTERFACE PRINCIPALE ---
st.title("📅 Planning IT - 2026")
env_selected = st.radio("Secteur :", ["PROD", "PRÉPROD", "RECETTE"], horizontal=True)

mois_noms = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
tabs = st.tabs(mois_noms)

# On définit les couleurs une seule fois
COLOR_MAP = {
    "MEP": "background-color: #0070C0; color: white; font-weight: bold",
    "INC": "background-color: #FF0000; color: white; font-weight: bold",
    "MAI": "background-color: #FFC000; color: black; font-weight: bold",
    "TES": "background-color: #00B050; color: white; font-weight: bold",
    "MOR": "background-color: #9600C8; color: white; font-weight: bold",
    "•": "background-color: #f1f3f4; color: transparent"
}

def apply_style(val):
    return COLOR_MAP.get(val, "")

for i, tab in enumerate(tabs):
    with tab:
        month_num = i + 1
        year = 2026
        num_days = calendar.monthrange(year, month_num)[1]
        dates = [date(year, month_num, d) for d in range(1, num_days + 1)]
        
        if not st.session_state.apps:
            st.info("Utilisez la barre latérale pour ajouter vos applications.")
        else:
            current_apps = sorted(st.session_state.apps)
            grid = {"App": current_apps}
            
            # Remplissage des données
            for d in dates:
                col = str(d.day)
                grid[col] = []
                for app in current_apps:
                    status = ""
                    if d.weekday() >= 5: status = "•"
                    for ev in st.session_state.events:
                        if ev['app'] == app and ev['env'] == env_selected:
                            if ev['d1'] <= d <= ev['d2']:
                                status = ev['type'][:3]
                    grid[col].append(status)
            
            df_display = pd.DataFrame(grid)

            # Configuration des colonnes
            c_config = {"App": st.column_config.TextColumn("Application", width="medium", pinned=True)}
            for d in dates:
                c_config[str(d.day)] = st.column_config.TextColumn(str(d.day), width=35)

            # Affichage du tableau interactif
            # Utilisation de selection_mode simple pour éviter les erreurs de version
            selection = st.dataframe(
                df_display.style.map(apply_style),
                use_container_width=True,
                hide_index=True,
                column_config=c_config,
                on_select="rerun",
                selection_mode=["single_row", "single_column"]
            )

            # --- 4. RÉCUPÉRATION DU CLIC PRÉCIS ---
            try:
                # Vérification de la présence d'une sélection
                s_rows = selection.selection.rows
                s_cols = selection.selection.columns

                if s_rows and s_cols:
                    row_idx = s_rows[0]
                    col_name = s_cols[0]

                    if col_name != "App":
                        selected_app = current_apps[row_idx]
                        day_num = int(col_name)
                        clicked_date = date(year, month_num, day_num)
                        
                        st.markdown(f"---")
                        st.markdown(f"### 🔍 Détails : {selected_app} ({day_num} {mois_noms[i]})")
                        
                        matches = [e for e in st.session_state.events if e['app'] == selected_app 
                                   and e['env'] == env_selected 
                                   and e['d1'] <= clicked_date <= e['d2']]
                        
                        if matches:
                            for e in matches:
                                with st.container(border=True):
                                    st.write(f"**Type :** {e['type']}")
                                    st.write(f"**Période :** du {e['d1']} au {e['d2']}")
                                    if e['comment']:
                                        st.info(f"**Commentaire :** {e['comment']}")
                        else:
                            st.write("Journée libre.")
                else:
                    st.caption("💡 Cliquez sur une case colorée pour voir le détail.")
            except Exception:
                st.caption("Sélectionnez une cellule pour afficher les détails.")
