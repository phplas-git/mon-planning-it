import streamlit as st
import pandas as pd
import calendar
from datetime import date

# ==================================================
# 1. CONFIGURATION
# ==================================================
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# Jours fériés 2026
JOURS_FERIES_2026 = [
    date(2026, 1, 1), date(2026, 4, 6), date(2026, 5, 1), date(2026, 5, 8),
    date(2026, 5, 14), date(2026, 5, 25), date(2026, 7, 14), date(2026, 8, 15),
    date(2026, 11, 1), date(2026, 11, 11), date(2026, 12, 25),
]

# Initialisation
if "apps" not in st.session_state: st.session_state.apps = []
if "events" not in st.session_state: st.session_state.events = []

# ==================================================
# 2. BARRE LATÉRALE
# ==================================================
with st.sidebar:
    st.header("⚙️ Admin")
    
    # Bouton de rafraîchissement rapide
    if st.button("🔄 Rafraîchir l'affichage"):
        st.rerun()
        
    with st.expander("Gestion Applications", expanded=True):
        with st.form("add_app", clear_on_submit=True):
            new_app = st.text_input("Nom de l'App").upper().strip()
            if st.form_submit_button("Ajouter") and new_app:
                if new_app not in st.session_state.apps:
                    st.session_state.apps.append(new_app)
                    st.rerun()

    st.divider()

    st.subheader("Nouvel Événement")
    if st.session_state.apps:
        with st.form("add_event", clear_on_submit=True):
            f_app = st.selectbox("App", sorted(st.session_state.apps))
            f_env = st.selectbox("Env", ["PROD", "PRÉPROD", "RECETTE"])
            f_type = st.selectbox("Type", ["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"])
            f_comm = st.text_area("Détails")
            c1, c2 = st.columns(2)
            d1 = c1.date_input("Du")
            d2 = c2.date_input("Au")

            if st.form_submit_button("Enregistrer"):
                st.session_state.events.append({
                    "app": f_app, "env": f_env, "type": f_type,
                    "d1": d1, "d2": d2, "comment": f_comm
                })
                st.success("Enregistré !")
                st.rerun()
    else:
        st.info("Ajoutez d'abord une application.")

    st.divider()
    if st.button("🗑️ Reset Tout"):
        st.session_state.apps, st.session_state.events = [], []
        st.rerun()

# ==================================================
# 3. CSS (Mixte : Design Pro + Tes Préférences)
# ==================================================
css = """
<style>
    .planning-container {
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        overflow-x: auto;
    }
    .planning-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        background-color: #ffffff;
    }
    
    /* EN-TÊTES */
    .planning-table th {
        background-color: #f1f5f9;
        color: #1e293b;
        padding: 10px 5px;
        text-align: center;
        border-right: 1px solid #e2e8f0;
        border-bottom: 2px solid #cbd5e1;
        font-size: 11px;
    }
    .planning-table th.app-header {
        text-align: left;
        padding-left: 15px;
        min-width: 120px;
        position: sticky;
        left: 0;
        z-index: 10;
        border-right: 2px solid #cbd5e1;
    }

    /* CELLULES */
    .planning-table td {
        background-color: #ffffff;
        text-align: center;
        padding: 0;
        height: 40px;
        border-right: 1px solid #f1f5f9;
        border-bottom: 1px solid #f1f5f9;
        cursor: pointer;
    }
    .planning-table td.app-name {
        background-color: #f8fafc;
        color: #0f172a;
        font-weight: bold;
        text-align: left;
        padding-left: 15px;
        border-right: 2px solid #cbd5e1;
        position: sticky;
        left: 0;
        z-index: 5;
    }

    /* WEEK-END & FÉRIÉS (Tes préférences) */
    .planning-table td.weekend {
        background-color: #e2e8f0 !important; /* Gris */
    }
    .planning-table td.ferie {
        background-color: #FFE6F0 !important; /* Rose pâle original */
        color: #000;
    }

    /* TYPES D'ÉVÉNEMENTS */
    .event-cell {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
        color: white; 
        font-weight: bold;
        font-size: 10px;
    }
    .mep { background-color: #0070C0; }
    .inc { background-color: #FF0000; }
    .mai { background-color: #FFC000; color: black; }
    .test { background-color: #00B050; }
    .mor { background-color: #9600C8; }

    /* TOOLTIP AVEC ICÔNES */
    .tooltip {
        position: relative;
        width: 100%;
        height: 100%;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 280px;
        background-color: #333;
        color: #fff;
        text-align: left;
        border-radius: 6px;
        padding: 10px;
        position: absolute;
        z-index: 100;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 12px;
        line-height: 1.6;
        pointer-events: none;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    /* Style des labels dans le tooltip */
    .tooltip-label {
        font-weight: bold;
        color: #4CAF50; /* Vert style Matrix/Code */
        margin-right: 5px;
    }
</style>
"""

# ==================================================
# 4. GÉNÉRATION
# ==================================================
st.title("📅 Planning IT – 2026")
env_selected = st.radio("Secteur :", ["PROD", "PRÉPROD", "RECETTE"], horizontal=True)

months = ["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
tabs = st.tabs(months)

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

        # Tableau HTML
        html = css + '<div class="planning-container"><table class="planning-table">'
        
        # Header
        html += '<thead><tr><th class="app-header">Application</th>'
        for d in dates:
            day_letter = ["L", "M", "M", "J", "V", "S", "D"][d.weekday()]
            html += f'<th>{d.day}<br><small>{day_letter}</small></th>'
        html += '</tr></thead><tbody>'

        # Corps
        for app in apps:
            html += f'<tr><td class="app-name">{app}</td>'
            
            for d in dates:
                classes = []
                content = ""
                tooltip_html = ""
                
                # Weekend
                if d.weekday() >= 5: classes.append("weekend")
                
                # Férié (Retour du confettis)
                if d in JOURS_FERIES_2026:
                    classes.append("ferie")
                    if not content: content = "🎉"

                # Recherche Event
                found_ev = None
                for ev in st.session_state.events:
                    if ev["app"] == app and ev["env"] == env_selected:
                        if ev["d1"] <= d <= ev["d2"]:
                            found_ev = ev
                            break
                
                if found_ev:
                    type_cls = ""
                    if found_ev["type"] == "MEP": type_cls = "mep"
                    elif found_ev["type"] == "INCIDENT": type_cls = "inc"
                    elif found_ev["type"] == "MAINTENANCE": type_cls = "mai"
                    elif found_ev["type"] == "TEST": type_cls = "test"
                    elif found_ev["type"] == "MORATOIRE": type_cls = "mor"
                    
                    short_txt = found_ev["type"][:3]
                    
                    # Tooltip (Retour des ICÔNES)
                    duree = (found_ev['d2'] - found_ev['d1']).days + 1
                    tooltip_html = f"""
                    <div class="tooltiptext">
                        <span class="tooltip-label">📱 Application:</span> {found_ev['app']}<br>
                        <span class="tooltip-label">🌐 Environnement:</span> {found_ev['env']}<br>
                        <span class="tooltip-label">🏷️ Type:</span> {found_ev['type']}<br>
                        <span class="tooltip-label">📅 Période:</span> Du {found_ev['d1'].strftime('%d/%m')} au {found_ev['d2'].strftime('%d/%m')}<br>
                        <span class="tooltip-label">⏱️ Durée:</span> {duree} j<br>
                        <span class="tooltip-label">💬 Note:</span> {found_ev['comment'] if found_ev['comment'] else '-'}
                    </div>
                    """
                    content = f'<div class="event-cell {type_cls}">{short_txt}</div>'
                
                td_cls = " ".join(classes)
                if tooltip_html:
                    html += f'<td class="{td_cls}"><div class="tooltip">{content}{tooltip_html}</div></td>'
                else:
                    html += f'<td class="{td_cls}">{content}</td>'
            
            html += '</tr>'
        html += '</tbody></table></div>'
        
        st.markdown(html, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="display:flex; gap:15px; font-size:12px; margin-top:10px; color:#666;">
            <span><span style="color:#0070C0">■</span> MEP</span>
            <span><span style="color:#FF0000">■</span> INCIDENT</span>
            <span><span style="color:#FFC000">■</span> MAINTENANCE</span>
            <span><span style="color:#e2e8f0">■</span> Week-End</span>
            <span><span style="color:#FFE6F0">■</span> Férié</span>
        </div>
        """, unsafe_allow_html=True)
