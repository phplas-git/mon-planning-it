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

# Initialisation des données
if "apps" not in st.session_state: st.session_state.apps = []
if "events" not in st.session_state: st.session_state.events = []

# ==================================================
# 2. BARRE LATÉRALE (ADMIN)
# ==================================================
with st.sidebar:
    st.header("⚙️ Admin")
    
    # Ajout App
    with st.expander("Gestion Applications", expanded=True):
        with st.form("add_app", clear_on_submit=True):
            new_app = st.text_input("Nom de l'App").upper().strip()
            if st.form_submit_button("Ajouter") and new_app:
                if new_app not in st.session_state.apps:
                    st.session_state.apps.append(new_app)
                    st.rerun()

    st.divider()

    # Ajout Event
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
# 3. STYLE CSS (LE DESIGN "JOLI")
# ==================================================
css = """
<style>
    /* Conteneur global du tableau */
    .planning-container {
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        font-size: 13px;
        overflow-x: auto;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
    }

    .planning-table {
        width: 100%;
        border-collapse: separate; /* Permet les bordures arrondies */
        border-spacing: 0;
        background-color: #ffffff;
    }

    /* --- EN-TÊTES (Gris bleuté) --- */
    .planning-table th {
        background-color: #f1f5f9; /* Gris très clair bleuté */
        color: #1e293b; /* Bleu nuit presque noir */
        padding: 12px 5px;
        text-align: center;
        border-right: 1px solid #e2e8f0;
        border-bottom: 2px solid #cbd5e1;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 11px;
    }

    /* Colonne Application (En-tête et Cellules) */
    .planning-table th.app-header {
        text-align: left;
        padding-left: 15px;
        min-width: 120px;
        position: sticky;
        left: 0;
        background-color: #f1f5f9;
        z-index: 10;
        border-right: 2px solid #cbd5e1;
    }
    
    .planning-table td.app-name {
        background-color: #f8fafc; /* Légèrement différent pour les lignes */
        color: #0f172a;
        font-weight: 700;
        text-align: left;
        padding-left: 15px;
        border-right: 2px solid #cbd5e1;
        border-bottom: 1px solid #e2e8f0;
        position: sticky;
        left: 0;
        z-index: 5;
    }

    /* --- CELLULES DE JOURS (Fond Blanc) --- */
    .planning-table td {
        background-color: #ffffff; /* BLANC PUR demandé */
        color: #334155;
        text-align: center;
        padding: 0;
        height: 45px; /* Hauteur confortable */
        border-right: 1px solid #f1f5f9;
        border-bottom: 1px solid #f1f5f9;
        transition: background-color 0.2s;
        cursor: pointer;
    }
    
    .planning-table td:hover {
        background-color: #f8fafc; /* Effet survol léger */
    }

    /* --- WEEK-ENDS (Gris marqué) --- */
    .planning-table td.weekend {
        background-color: #e2e8f0 !important; /* Gris moyen */
        background-image: repeating-linear-gradient(45deg, transparent, transparent 5px, rgba(255,255,255,0.5) 5px, rgba(255,255,255,0.5) 10px);
    }

    /* --- JOURS FÉRIÉS (Rose pâle) --- */
    .planning-table td.ferie {
        background-color: #fff1f2 !important;
        border-bottom: 2px solid #fda4af;
    }

    /* --- TYPES D'ÉVÉNEMENTS (Couleurs vives) --- */
    .event-cell {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
        font-weight: bold;
        font-size: 10px;
        color: white;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.2);
    }
    .mep { background-color: #0ea5e9; } /* Bleu Cyan */
    .inc { background-color: #ef4444; } /* Rouge */
    .mai { background-color: #f59e0b; color: black; } /* Orange/Jaune */
    .test { background-color: #10b981; } /* Vert Emeraude */
    .mor { background-color: #8b5cf6; } /* Violet */

    /* --- TOOLTIP (Info-bulle Moderne) --- */
    .tooltip {
        position: relative;
        width: 100%;
        height: 100%;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 250px;
        background-color: #1e293b; /* Fond sombre pro */
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
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        font-size: 12px;
        line-height: 1.5;
        pointer-events: none;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    .badge {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: bold;
        margin-bottom: 5px;
    }
</style>
"""

# ==================================================
# 4. GÉNÉRATION DU PLANNING HTML
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
            st.info("👋 Aucune application. Ajoutez-en une dans le menu à gauche.")
            continue

        apps = sorted(st.session_state.apps)

        # Début du tableau
        html = css + '<div class="planning-container"><table class="planning-table">'
        
        # --- HEADER (Jours) ---
        html += '<thead><tr><th class="app-header">Application</th>'
        for d in dates:
            day_letter = ["L", "M", "M", "J", "V", "S", "D"][d.weekday()]
            # On met le numéro en gros et la lettre en petit
            html += f'<th>{d.day}<div style="font-size:9px; color:#64748b;">{day_letter}</div></th>'
        html += '</tr></thead><tbody>'

        # --- CORPS (Lignes Apps) ---
        for app in apps:
            html += f'<tr><td class="app-name">{app}</td>'
            
            for d in dates:
                classes = []
                content = ""
                tooltip_html = ""
                
                # Gestion Weekend
                if d.weekday() >= 5: classes.append("weekend")
                
                # Gestion Férié
                if d in JOURS_FERIES_2026:
                    classes.append("ferie")
                    if not content: content = "★"

                # Recherche Événement
                found_ev = None
                for ev in st.session_state.events:
                    if ev["app"] == app and ev["env"] == env_selected:
                        if ev["d1"] <= d <= ev["d2"]:
                            found_ev = ev
                            break
                
                # Construction Cellule
                if found_ev:
                    type_cls = ""
                    if found_ev["type"] == "MEP": type_cls = "mep"
                    elif found_ev["type"] == "INCIDENT": type_cls = "inc"
                    elif found_ev["type"] == "MAINTENANCE": type_cls = "mai"
                    elif found_ev["type"] == "TEST": type_cls = "test"
                    elif found_ev["type"] == "MORATOIRE": type_cls = "mor"
                    
                    short_txt = found_ev["type"][:3]
                    
                    # Tooltip HTML
                    tooltip_html = f"""
                    <div class="tooltiptext">
                        <span class="badge {type_cls}" style="color:white; background:rgba(255,255,255,0.2);">{found_ev['type']}</span><br>
                        <strong>{found_ev['app']}</strong><br>
                        Du {found_ev['d1'].strftime('%d/%m')} au {found_ev['d2'].strftime('%d/%m')}<br>
                        <em>{found_ev['comment'] if found_ev['comment'] else 'Aucun détail'}</em>
                    </div>
                    """
                    
                    content = f'<div class="event-cell {type_cls}">{short_txt}</div>'
                
                # Assemblage final de la case
                td_cls = " ".join(classes)
                if tooltip_html:
                    html += f'<td class="{td_cls}"><div class="tooltip">{content}{tooltip_html}</div></td>'
                else:
                    html += f'<td class="{td_cls}">{content}</td>'
            
            html += '</tr>'
        
        html += '</tbody></table></div>'
        
        st.markdown(html, unsafe_allow_html=True)
        
        # Légende propre
        st.markdown("""
        <div style="display:flex; gap:15px; font-size:12px; margin-top:10px; color:#64748b;">
            <span style="display:flex; align-items:center;"><div style="width:10px; height:10px; background:#0ea5e9; margin-right:5px; border-radius:2px;"></div> MEP</span>
            <span style="display:flex; align-items:center;"><div style="width:10px; height:10px; background:#ef4444; margin-right:5px; border-radius:2px;"></div> INCIDENT</span>
            <span style="display:flex; align-items:center;"><div style="width:10px; height:10px; background:#f59e0b; margin-right:5px; border-radius:2px;"></div> MAINTENANCE</span>
            <span style="display:flex; align-items:center;"><div style="width:10px; height:10px; background:#e2e8f0; margin-right:5px; border-radius:2px;"></div> Week-End</span>
        </div>
        """, unsafe_allow_html=True)
