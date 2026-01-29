import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# Initialisation robuste
if 'events' not in st.session_state: st.session_state.events = []
if 'apps' not in st.session_state: st.session_state.apps = []

# --- 2. BARRE LATÉRALE ---
with st.sidebar:
    st.title("⚙️ Administration")
    
    # Section Ajout App - Sortie du expander pour plus de stabilité
    st.subheader("🚀 Gérer les Applications")
    new_app = st.text_input("Nom de l'appli (ex: PRAC)", key="input_new_app").upper()
    if st.button("Ajouter l'Application"):
        if new_app:
            if new_app not in st.session_state.apps:
                st.session_state.apps.append(new_app)
                st.success(f"Appli {new_app} ajoutée !")
                st.rerun()
            else:
                st.warning("Cette application existe déjà.")
        else:
            st.error("Veuillez saisir un nom.")

    st.divider()
    
    st.subheader("➕ Nouvel Événement")
    # On sécurise la liste des options
    app_options = sorted(st.session_state.apps) if st.session_state.apps else []
    
    with st.form("add_event", clear_on_submit=True):
        f_app = st.selectbox("Application", options=app_options if app_options else ["Aucune application"])
        f_env = st.selectbox("Environnement", ["PROD", "PRÉPROD", "RECETTE"])
        f_type = st.selectbox("Type", ["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"])
        f_comment = st.text_area("Commentaire / Détails")
        col1, col2 = st.columns(2)
        f_d1 = col1.date_input("Début")
        f_d2 = col2.date_input("Fin")
        submit = st.form_submit_button("Enregistrer l'événement")
        
        if submit:
            if not st.session_state.apps:
                st.error("Ajoutez d'abord une application !")
            else:
                st.session_state.events.append({
                    'app': f_app, 'env': f_env, 'type': f_type, 
                    'd1': f_d1, 'd2': f_d2, 'comment': f_comment
                })
                st.success("Événement enregistré !")
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
            st.info("👋 Bienvenue ! Commencez par ajouter une application dans la barre latérale à gauche.")
        else:
            # On trie une seule fois ici pour tout le bloc
            current_apps = sorted(st.session_state.apps)
            
            grid_data = {"App": current_apps}
            for d in dates:
                col_name = str(d.day)
                grid_data[col_name] = []
                for app in current_apps:
                    val = ""
                    if d.weekday() >= 5: val = "•"
                    for ev in st.session_state.events:
                        if ev['app'] == app and ev['env'] == env_selected:
                            if ev['d1'] <= d <= ev['d2']:
                                val = ev['type'][:3]
                    grid_data[col_name].append(val)
            
            df = pd.DataFrame(grid_data)

            # Style (Version compatible Pandas 2.x)
            def color_excel(val):
                if val == "MEP": return "background-color: #0070C0; color: white; font-weight: bold"
                if val == "INC": return "background-color: #FF0000; color: white; font-weight: bold"
                if val == "MAI": return "background-color: #FFC000; color: black; font-weight: bold"
                if val == "TES": return "background-color: #00B050; color: white; font-weight: bold"
                if val == "MOR": return "background-color: #9600C8; color: white; font-weight: bold"
                if val == "•": return "background-color: #f1f3f4; color: transparent"
                return ""

            # Config Colonnes
            config_cols = {"App": st.column_config.TextColumn("Application", width="medium", pinned=True)}
            for d in dates:
                config_cols[str(d.day)] = st.column_config.TextColumn(str(d.day), width=35)

            # Affichage
            result = st.dataframe(
                df.style.map(color_excel),
                use_container_width=True,
                hide_index=True,
                column_config=config_cols,
                on_select="rerun",
                selection_mode=["single_row", "single_column"]
            )

            # --- 4. LOGIQUE DE DÉTAILS ---
            selected_rows = result.selection.rows
            selected_cols = result.selection.columns

            if selected_rows and selected_cols:
                row_idx = selected_rows[0]
                col_name = selected_cols[0]

                if col_name != "App":
                    selected_app = current_apps[row_idx]
                    day_clicked = int(col_name)
                    target_date = date(year, month_num, day_clicked)
                    
                    st.divider()
                    st.subheader(f"🔍 Détails : {selected_app} ({day_clicked} {mois_noms[i]})")
                    
                    matches = [e for e in st.session_state.events if e['app'] == selected_app 
                               and e['env'] == env_selected 
                               and e['d1'] <= target_date <= e['d2']]
                    
                    if matches:
                        for e in matches:
                            with st.container(border=True):
                                c1, c2 = st.columns([1, 4])
                                c1.metric("TYPE", e['type'])
                                c2.markdown(f"**Période :** du {e['d1'].strftime('%d/%m')} au {e['d2'].strftime('%d/%m')}")
                                if e['comment']:
                                    c2.info(f"**Commentaire :** {e['comment']}")
                    else:
                        st.write("Rien de prévu ce jour-là.")
