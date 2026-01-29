import streamlit as st
import pandas as pd
import calendar
from datetime import date

# ==================================================
# CONFIGURATION PAGE
# ==================================================
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# ==================================================
# SESSION STATE
# ==================================================
if "apps" not in st.session_state:
    st.session_state.apps = []

if "events" not in st.session_state:
    st.session_state.events = []

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:
    st.title("⚙️ Admin")

    # ---- Ajouter Application
    with st.form("add_app", clear_on_submit=True):
        new_app = st.text_input("Application").upper().strip()
        if st.form_submit_button("Ajouter") and new_app:
            if new_app not in st.session_state.apps:
                st.session_state.apps.append(new_app)
                st.rerun()

    st.divider()

    # ---- Ajouter Événement
    if st.session_state.apps:
        with st.form("add_event", clear_on_submit=True):
            f_app = st.selectbox("App", st.session_state.apps)
            f_env = st.selectbox("Env", ["PROD", "PRÉPROD", "RECETTE"])
            f_type = st.selectbox("Type", ["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"])
            f_comm = st.text_area("Détails")
            c1, c2 = st.columns(2)
            d1 = c1.date_input("Du")
            d2 = c2.date_input("Au")

            if st.form_submit_button("Enregistrer"):
                st.session_state.events.append({
                    "app": f_app,
                    "env": f_env,
                    "type": f_type,
                    "d1": d1,
                    "d2": d2,
                    "comment": f_comm
                })
                st.success("Événement enregistré")
                st.rerun()

    if st.button("Tout effacer"):
        st.session_state.apps = []
        st.session_state.events = []
        st.rerun()

# ==================================================
# MAIN
# ==================================================
st.title("📅 Planning IT – 2026")
env_selected = st.radio("Vue :", ["PROD", "PRÉPROD", "RECETTE"], horizontal=True)

months = [
    "Janvier","Février","Mars","Avril","Mai","Juin",
    "Juillet","Août","Septembre","Octobre","Novembre","Décembre"
]
tabs = st.tabs(months)

# ==================================================
# STYLE CELLULE
# ==================================================
def get_cell_style(val):
    styles = {
        "MEP": "background-color:#0070C0;color:white;font-weight:bold",
        "INC": "background-color:#FF0000;color:white;font-weight:bold",
        "MAI": "background-color:#FFC000;color:black;font-weight:bold",
        "TES": "background-color:#00B050;color:white;font-weight:bold",
        "MOR": "background-color:#9600C8;color:white;font-weight:bold",
        "•": "background-color:#f0f0f0;color:#d0d0d0"
    }
    return styles.get(val, "")

# ==================================================
# TABLES PAR MOIS
# ==================================================
for i, tab in enumerate(tabs):
    with tab:
        year = 2026
        month = i + 1
        nb_days = calendar.monthrange(year, month)[1]
        dates = [date(year, month, d) for d in range(1, nb_days + 1)]

        if not st.session_state.apps:
            st.info("Ajoutez une application pour commencer.")
            continue

        apps = sorted(st.session_state.apps)
        data = {"App": apps}

        # ---- Remplissage des données
        for d in dates:
            col = str(d.day)
            data[col] = []
            for app in apps:
                val = "•" if d.weekday() >= 5 else ""
                for ev in st.session_state.events:
                    if ev["app"] == app and ev["env"] == env_selected:
                        if ev["d1"] <= d <= ev["d2"]:
                            val = ev["type"][:3]
                data[col].append(val)

        df = pd.DataFrame(data)

        # ---- Configuration des colonnes
        column_config = {"App": st.column_config.TextColumn("App", width="medium")}
        for col in df.columns:
            if col != "App":
                column_config[col] = st.column_config.TextColumn(col, width="small")

        # ---- Data editor
        key_editor = f"editor_{env_selected}_{i}"

        edited_df = st.data_editor(
            df,
            hide_index=True,
            column_config=column_config,
            key=key_editor,
            use_container_width=True,
            disabled=True,
            on_change=None
        )

        # ---- DEBUG: Afficher l'état de la sélection
        editor_state = st.session_state.get(key_editor)
        
        st.write("DEBUG - État du data_editor:", editor_state)  # Pour debug
        
        # ---- Lecture de la sélection (plusieurs méthodes)
        selected_cells = None
        selected_rows = None
        
        if editor_state:
            # Méthode 1: selected_cells
            if isinstance(editor_state, dict) and "selected_cells" in editor_state:
                selected_cells = editor_state["selected_cells"]
            
            # Méthode 2: selection avec rows
            if isinstance(editor_state, dict) and "selection" in editor_state:
                selection = editor_state["selection"]
                if "rows" in selection and selection["rows"]:
                    selected_rows = list(selection["rows"])

        # ---- Affichage des détails si sélection
        if selected_cells and len(selected_cells) > 0:
            cell = selected_cells[0]
            row_idx = cell["row"]
            col_name = cell["column"]
            
            st.write(f"DEBUG - Cellule sélectionnée: ligne {row_idx}, colonne {col_name}")  # Pour debug

            if col_name != "App":
                sel_app = df.iloc[row_idx]["App"]
                sel_day = int(col_name)
                sel_date = date(year, month, sel_day)

                st.divider()
                st.subheader(f"🔍 Détail : {sel_app} — {sel_day} {months[i]} {year}")

                # Rechercher l'événement correspondant
                found = False
                for ev in st.session_state.events:
                    if ev["app"] == sel_app and ev["env"] == env_selected:
                        if ev["d1"] <= sel_date <= ev["d2"]:
                            found = True
                            with st.container(border=True):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.metric("📱 Application", ev["app"])
                                    st.metric("🌐 Environnement", ev["env"])
                                    st.metric("🏷️ Type", ev["type"])
                                
                                with col2:
                                    st.metric("📅 Date début", ev['d1'].strftime('%d/%m/%Y'))
                                    st.metric("📅 Date fin", ev['d2'].strftime('%d/%m/%Y'))
                                    duree = (ev['d2'] - ev['d1']).days + 1
                                    st.metric("⏱️ Durée", f"{duree} jour(s)")
                                
                                if ev["comment"]:
                                    st.markdown("**💬 Commentaire :**")
                                    st.info(ev["comment"])
                                else:
                                    st.caption("_Aucun commentaire_")

                if not found:
                    st.info("Aucun événement prévu ce jour-là.")
                    
        elif selected_rows and len(selected_rows) > 0:
            row_idx = selected_rows[0]
            sel_app = df.iloc[row_idx]["App"]
            
            st.divider()
            st.subheader(f"🔍 Événements pour {sel_app} - {months[i]} {year}")

            events_found = [
                ev for ev in st.session_state.events
                if ev["app"] == sel_app and ev["env"] == env_selected
                and ((ev["d1"].year == year and ev["d1"].month == month) or 
                     (ev["d2"].year == year and ev["d2"].month == month) or
                     (ev["d1"] <= date(year, month, 1) and ev["d2"] >= date(year, month, nb_days)))
            ]

            if events_found:
                for ev in events_found:
                    with st.container(border=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("📱 Application", ev["app"])
                            st.metric("🌐 Environnement", ev["env"])
                            st.metric("🏷️ Type", ev["type"])
                        
                        with col2:
                            st.metric("📅 Date début", ev['d1'].strftime('%d/%m/%Y'))
                            st.metric("📅 Date fin", ev['d2'].strftime('%d/%m/%Y'))
                            duree = (ev['d2'] - ev['d1']).days + 1
                            st.metric("⏱️ Durée", f"{duree} jour(s)")
                        
                        if ev["comment"]:
                            st.markdown("**💬 Commentaire :**")
                            st.info(ev["comment"])
                        else:
                            st.caption("_Aucun commentaire_")
            else:
                st.info("Aucun événement ce mois-ci.")
        else:
            st.caption("👆 Cliquez sur une cellule du tableau pour voir les détails de l'événement.")
