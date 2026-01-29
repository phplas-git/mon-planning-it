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

if "selected_event" not in st.session_state:
    st.session_state.selected_event = None

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
        st.session_state.selected_event = None
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
def get_cell_color(val):
    colors = {
        "MEP": "#0070C0",
        "INC": "#FF0000",
        "MAI": "#FFC000",
        "TES": "#00B050",
        "MOR": "#9600C8",
    }
    return colors.get(val, "#f0f0f0")

def get_text_color(val):
    if val in ["MEP", "INC", "TES", "MOR"]:
        return "white"
    elif val == "MAI":
        return "black"
    return "#d0d0d0"

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

        # ---- Création du tableau HTML avec boutons
        html = """
        <style>
            .planning-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 11px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }
            .planning-table th {
                border: 1px solid #ddd;
                padding: 6px;
                background-color: #f2f2f2;
                font-weight: bold;
                text-align: center;
                position: sticky;
                top: 0;
            }
            .planning-table td {
                border: 1px solid #ddd;
                padding: 4px;
                text-align: center;
                height: 30px;
            }
            .planning-table td.app-name {
                text-align: left;
                font-weight: bold;
                background-color: #f9f9f9;
            }
        </style>
        <table class="planning-table">
            <tr>
                <th>App</th>
        """
        
        # En-têtes des jours
        for d in range(1, nb_days + 1):
            html += f"<th>{d}</th>"
        html += "</tr>"

        # Lignes par application
        for app in apps:
            html += f"<tr><td class='app-name'>{app}</td>"
            
            for d in dates:
                day_num = d.day
                val = "•" if d.weekday() >= 5 else ""
                event_id = None
                
                # Trouver l'événement pour cette cellule
                for idx, ev in enumerate(st.session_state.events):
                    if ev["app"] == app and ev["env"] == env_selected:
                        if ev["d1"] <= d <= ev["d2"]:
                            val = ev["type"][:3]
                            event_id = idx
                            break
                
                bg_color = get_cell_color(val)
                text_color = get_text_color(val)
                
                html += f"<td style='background-color:{bg_color}; color:{text_color}; font-weight:bold;'>{val}</td>"
            
            html += "</tr>"
        
        html += "</table>"
        
        st.markdown(html, unsafe_allow_html=True)
        
        st.divider()
        
        # ---- Liste des événements avec boutons cliquables
        st.subheader(f"📋 Liste des événements - {months[i]} {year}")
        
        events_this_month = [
            (idx, ev) for idx, ev in enumerate(st.session_state.events)
            if ev["env"] == env_selected
            and ((ev["d1"].year == year and ev["d1"].month == month) or 
                 (ev["d2"].year == year and ev["d2"].month == month) or
                 (ev["d1"] <= date(year, month, 1) and ev["d2"] >= date(year, month, nb_days)))
        ]
        
        if events_this_month:
            cols = st.columns(min(3, len(events_this_month)))
            
            for col_idx, (ev_idx, ev) in enumerate(events_this_month):
                with cols[col_idx % 3]:
                    # Couleur du bouton selon le type
                    type_colors = {
                        "MEP": "🔵",
                        "INCIDENT": "🔴",
                        "MAINTENANCE": "🟡",
                        "TEST": "🟢",
                        "MORATOIRE": "🟣"
                    }
                    icon = type_colors.get(ev["type"], "⚪")
                    
                    if st.button(
                        f"{icon} {ev['app']} - {ev['type'][:3]}",
                        key=f"btn_{i}_{ev_idx}",
                        use_container_width=True
                    ):
                        st.session_state.selected_event = ev_idx
                        st.rerun()
        else:
            st.info("Aucun événement ce mois-ci")
        
        # ---- Affichage du détail de l'événement sélectionné
        if st.session_state.selected_event is not None:
            if st.session_state.selected_event < len(st.session_state.events):
                ev = st.session_state.events[st.session_state.selected_event]
                
                # Vérifier que l'événement est bien dans le bon mois et environnement
                is_in_month = ((ev["d1"].year == year and ev["d1"].month == month) or 
                              (ev["d2"].year == year and ev["d2"].month == month) or
                              (ev["d1"] <= date(year, month, 1) and ev["d2"] >= date(year, month, nb_days)))
                
                if ev["env"] == env_selected and is_in_month:
                    st.divider()
                    st.subheader("🔍 Détail de l'événement")
                    
                    with st.container(border=True):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("📱 Application", ev["app"])
                            st.metric("🌐 Environnement", ev["env"])
                        
                        with col2:
                            st.metric("🏷️ Type", ev["type"])
                            duree = (ev['d2'] - ev['d1']).days + 1
                            st.metric("⏱️ Durée", f"{duree} jour(s)")
                        
                        with col3:
                            st.metric("📅 Date début", ev['d1'].strftime('%d/%m/%Y'))
                            st.metric("📅 Date fin", ev['d2'].strftime('%d/%m/%Y'))
                        
                        if ev["comment"]:
                            st.markdown("---")
                            st.markdown("**💬 Commentaire :**")
                            st.info(ev["comment"])
                        else:
                            st.markdown("---")
                            st.caption("_Aucun commentaire_")
                        
                        if st.button("✖️ Fermer", key=f"close_{i}"):
                            st.session_state.selected_event = None
                            st.rerun()
