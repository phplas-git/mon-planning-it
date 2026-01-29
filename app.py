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

if "selected_cell" not in st.session_state:
    st.session_state.selected_cell = None

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
        st.session_state.selected_cell = None
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

        # ---- Data editor SANS style (c'est ça le problème !)
        key_editor = f"editor_{env_selected}_{i}"

        edited_df = st.data_editor(
            df,
            hide_index=True,
            column_config=column_config,
            key=key_editor,
            use_container_width=True,
            disabled=True  # Désactive l'édition mais permet la sélection
        )

        # ---- Affichage du style avec HTML pour visualisation
        st.markdown("---")
        
        # Générer le HTML stylé pour affichage
        html = "<table style='width:100%; border-collapse: collapse; font-size: 12px;'>"
        html += "<tr>"
        for col in df.columns:
            html += f"<th style='border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;'>{col}</th>"
        html += "</tr>"
        
        for idx, row in df.iterrows():
            html += "<tr>"
            for col in df.columns:
                val = row[col]
                style = get_cell_style(val)
                html += f"<td style='border: 1px solid #ddd; padding: 8px; text-align: center; {style}'>{val}</td>"
            html += "</tr>"
        html += "</table>"
        
        with st.expander("📊 Vue stylée du planning"):
            st.markdown(html, unsafe_allow_html=True)

        # ---- Lecture de la sélection
        selection = st.session_state.get(key_editor, {})
        
        if "selection" in selection and selection["selection"]["rows"]:
            row_idx = list(selection["selection"]["rows"])[0]
            sel_app = df.iloc[row_idx]["App"]
            
            st.divider()
            st.subheader(f"🔍 Événements pour {sel_app} - {months[i]}")

            events_found = [
                ev for ev in st.session_state.events
                if ev["app"] == sel_app and ev["env"] == env_selected
                and (ev["d1"].month == month or ev["d2"].month == month)
            ]

            if events_found:
                for ev in events_found:
                    with st.container(border=True):
                        cols = st.columns([1, 3])
                        with cols[0]:
                            st.metric("TYPE", ev["type"])
                        with cols[1]:
                            st.markdown(
                                f"📅 **Du {ev['d1'].strftime('%d/%m/%Y')} "
                                f"au {ev['d2'].strftime('%d/%m/%Y')}**"
                            )
                        if ev["comment"]:
                            st.info(ev["comment"])
                        else:
                            st.caption("Pas de commentaire.")
            else:
                st.caption("Aucun événement ce mois-ci.")
        else:
            st.caption("👆 Sélectionnez une ligne (cliquez sur le numéro de ligne à gauche) pour voir les détails.")
