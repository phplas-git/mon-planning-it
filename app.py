import streamlit as st
import pandas as pd
import calendar
from datetime import date

# ==================================================
# CONFIGURATION PAGE
# ==================================================
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# ==================================================
# JOURS FÉRIÉS 2026 (France)
# ==================================================
JOURS_FERIES_2026 = [
    date(2026, 1, 1),   # Nouvel an
    date(2026, 4, 6),   # Lundi de Pâques
    date(2026, 5, 1),   # Fête du travail
    date(2026, 5, 8),   # Victoire 1945
    date(2026, 5, 14),  # Ascension
    date(2026, 5, 25),  # Lundi de Pentecôte
    date(2026, 7, 14),  # Fête nationale
    date(2026, 8, 15),  # Assomption
    date(2026, 11, 1),  # Toussaint
    date(2026, 11, 11), # Armistice
    date(2026, 12, 25), # Noël
]

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
# STYLE & TOOLTIP CSS
# ==================================================
css = """
<style>
    .planning-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        table-layout: fixed;
    }
    .planning-table th {
        border: 1px solid #ddd;
        padding: 8px;
        background-color: #f2f2f2;
        font-weight: bold;
        text-align: center;
        font-size: 11px;
    }
    .planning-table th.app-header {
        width: 120px;
        text-align: left;
    }
    .planning-table td {
        border: 1px solid #ddd;
        padding: 6px;
        text-align: center;
        font-weight: bold;
        position: relative;
        height: 35px;
        cursor: pointer;
    }
    .planning-table td.app-name {
        text-align: left;
        font-weight: bold;
        background-color: #f9f9f9;
    }
    .planning-table td.weekend {
        background-color: #f0f0f0;
        color: #999;
    }
    .planning-table td.ferie {
        background-color: #FFE6F0;
    }
    .planning-table td.mep {
        background-color: #0070C0;
        color: white;
    }
    .planning-table td.inc {
        background-color: #FF0000;
        color: white;
    }
    .planning-table td.mai {
        background-color: #FFC000;
        color: black;
    }
    .planning-table td.tes {
        background-color: #00B050;
        color: white;
    }
    .planning-table td.mor {
        background-color: #9600C8;
        color: white;
    }
    
    /* Tooltip */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 300px;
        background-color: #333;
        color: #fff;
        text-align: left;
        border-radius: 6px;
        padding: 12px;
        position: absolute;
        z-index: 9999;
        bottom: 125%;
        left: 50%;
        margin-left: -150px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 13px;
        line-height: 1.6;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .tooltip .tooltiptext::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: #333 transparent transparent transparent;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    .tooltip-label {
        display: block;
        font-weight: bold;
        margin-top: 8px;
        color: #4CAF50;
    }
    .tooltip-label:first-child {
        margin-top: 0;
    }
</style>
"""

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

        # ---- Création du tableau HTML avec tooltips
        html = css + '<table class="planning-table"><thead><tr><th class="app-header">Application</th>'
        
        # En-têtes des jours
        for d in dates:
            day_name = ["L", "M", "M", "J", "V", "S", "D"][d.weekday()]
            html += f'<th>{d.day}<br><small>{day_name}</small></th>'
        html += '</tr></thead><tbody>'

        # Lignes par application
        for app in apps:
            html += f'<tr><td class="app-name">{app}</td>'
            
            for d in dates:
                # Déterminer le type de cellule
                classes = []
                cell_content = ""
                tooltip_content = ""
                
                # Weekend
                if d.weekday() >= 5:
                    classes.append("weekend")
                    cell_content = "•"
                
                # Jour férié
                if d in JOURS_FERIES_2026:
                    classes.append("ferie")
                    if not cell_content:
                        cell_content = "🎉"
                
                # Chercher un événement
                event_found = None
                for ev in st.session_state.events:
                    if ev["app"] == app and ev["env"] == env_selected:
                        if ev["d1"] <= d <= ev["d2"]:
                            event_found = ev
                            break
                
                if event_found:
                    ev = event_found
                    type_short = ev["type"][:3].upper()
                    cell_content = type_short
                    
                    # Classes CSS selon le type
                    if ev["type"] == "MEP":
                        classes.append("mep")
                    elif ev["type"] == "INCIDENT":
                        classes.append("inc")
                    elif ev["type"] == "MAINTENANCE":
                        classes.append("mai")
                    elif ev["type"] == "TEST":
                        classes.append("tes")
                    elif ev["type"] == "MORATOIRE":
                        classes.append("mor")
                    
                    # Contenu du tooltip
                    duree = (ev['d2'] - ev['d1']).days + 1
                    tooltip_content = f'''
                    <span class="tooltiptext">
                        <span class="tooltip-label">📱 Application:</span> {ev["app"]}
                        <span class="tooltip-label">🌐 Environnement:</span> {ev["env"]}
                        <span class="tooltip-label">🏷️ Type:</span> {ev["type"]}
                        <span class="tooltip-label">📅 Période:</span> Du {ev["d1"].strftime("%d/%m/%Y")} au {ev["d2"].strftime("%d/%m/%Y")}
                        <span class="tooltip-label">⏱️ Durée:</span> {duree} jour(s)
                        {f'<span class="tooltip-label">💬 Commentaire:</span> {ev["comment"]}' if ev["comment"] else ''}
                    </span>
                    '''
                
                class_str = ' '.join(classes) if classes else ''
                
                if tooltip_content:
                    html += f'<td class="{class_str}"><div class="tooltip">{cell_content}{tooltip_content}</div></td>'
                else:
                    html += f'<td class="{class_str}">{cell_content}</td>'
            
            html += '</tr>'
        
        html += '</tbody></table>'
        
        st.markdown(html, unsafe_allow_html=True)
        
        st.caption("💡 Astuce : Survolez une cellule d'événement pour voir tous les détails")
