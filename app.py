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
# 2. LOGIQUE ADMIN / USER (Sidebar)
# ==================================================
with st.sidebar:
    st.title("🔒 Accès")
    
    # Bouton de rafraîchissement global
    if st.button("🔄 Rafraîchir"):
        st.rerun()
    
    st.divider()

    # --- SÉLECTEUR DE MODE ---
    mode_admin = st.toggle("Mode Admin")

    if mode_admin:
        # --- ZONE ADMIN ---
        password = st.text_input("Mot de passe", type="password")
        
        if password == "admin123":  # <--- MOT DE PASSE ICI
            st.success("Connecté en Admin")
            
            tab_adm_app, tab_adm_evt = st.tabs(["📱 Apps", "📅 Events"])
            
            # 1. GESTION DES APPLICATIONS (Ordre + Ajout + Suppr)
            with tab_adm_app:
                st.caption("Modifiez, ajoutez ou supprimez des lignes. L'ordre du tableau définit l'ordre d'affichage.")
                
                # Conversion liste -> DataFrame pour l'éditeur
                df_apps = pd.DataFrame(st.session_state.apps, columns=["Nom"])
                
                edited_df = st.data_editor(
                    df_apps, 
                    num_rows="dynamic", 
                    use_container_width=True,
                    hide_index=True,
                    key="editor_apps"
                )
                
                # Sauvegarde automatique si changement
                new_list = [x.upper().strip() for x in edited_df["Nom"].tolist() if x]
                if new_list != st.session_state.apps:
                    st.session_state.apps = new_list
                    st.rerun()

            # 2. GESTION DES ÉVÉNEMENTS (Liste globale)
            with tab_adm_evt:
                st.caption("Gérez tous les événements ici.")
                if st.session_state.events:
                    df_evts = pd.DataFrame(st.session_state.events)
                    
                    # Configuration des colonnes pour l'édition
                    column_cfg = {
                        "app": st.column_config.SelectboxColumn("App", options=st.session_state.apps, required=True),
                        "env": st.column_config.SelectboxColumn("Env", options=["PROD", "PRÉPROD", "RECETTE"], required=True),
                        "type": st.column_config.SelectboxColumn("Type", options=["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"], required=True),
                        "d1": st.column_config.DateColumn("Début", required=True),
                        "d2": st.column_config.DateColumn("Fin", required=True),
                        "comment": st.column_config.TextColumn("Détails")
                    }

                    edited_evts = st.data_editor(
                        df_evts, 
                        num_rows="dynamic", 
                        use_container_width=True,
                        column_config=column_cfg,
                        hide_index=True,
                        key="editor_events"
                    )

                    # Sauvegarde
                    # On convertit en liste de dicts pour le session_state
                    # On doit convertir les dates pandas en date python si nécessaire
                    if st.button("Sauvegarder les modifications"):
                        # Reconversion propre
                        cleaned_events = []
                        for index, row in edited_evts.iterrows():
                            cleaned_events.append({
                                "app": row["app"],
                                "env": row["env"],
                                "type": row["type"],
                                "d1": row["d1"], # data_editor retourne déjà des dates ou timestamps
                                "d2": row["d2"],
                                "comment": row["comment"]
                            })
                        st.session_state.events = cleaned_events
                        st.success("Planning mis à jour !")
                        st.rerun()
                else:
                    st.info("Aucun événement à gérer.")

            st.divider()
            if st.button("🗑️ RESET TOTAL (Danger)"):
                st.session_state.apps = []
                st.session_state.events = []
                st.rerun()

        elif password:
            st.error("Mot de passe incorrect")

    else:
        # --- ZONE UTILISATEUR SIMPLE ---
        st.subheader("➕ Nouvel Événement")
        
        if not st.session_state.apps:
            st.warning("Aucune application disponible. Demandez à l'admin d'en créer.")
        else:
            with st.form("add_event_user", clear_on_submit=True):
                # On utilise la liste définie par l'admin (et son ordre)
                f_app = st.selectbox("App", st.session_state.apps)
                f_env = st.selectbox("Env", ["PROD", "PRÉPROD", "RECETTE"])
                f_type = st.selectbox("Type", ["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"])
                f_comm = st.text_area("Détails")
                c1, c2 = st.columns(2)
                d1 = c1.date_input("Du")
                d2 = c2.date_input("Au")

                if st.form_submit_button("Ajouter au planning"):
                    st.session_state.events.append({
                        "app": f_app, "env": f_env, "type": f_type,
                        "d1": d1, "d2": d2, "comment": f_comm
                    })
                    st.success("✅ Ajouté !")
                    st.rerun()

# ==================================================
# 3. CSS & AFFICHAGE (Rien ne change ici)
# ==================================================
st.markdown("""
<style>
    .planning-wrap {
        overflow-x: auto;
        padding-bottom: 50px;
        margin-bottom: 20px;
    }
    .planning-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
        table-layout: fixed;
    }
    .planning-table th {
        background-color: #f8fafc;
        color: #334155;
        padding: 10px 5px;
        text-align: center;
        border-right: 1px solid #e2e8f0;
        border-bottom: 2px solid #cbd5e1;
        font-weight: 600;
        font-size: 11px;
    }
    .planning-table th.app-header {
        text-align: left;
        padding-left: 15px;
        width: 150px;
        position: sticky;
        left: 0;
        z-index: 20;
        background-color: #f8fafc;
        border-right: 2px solid #cbd5e1;
    }
    .planning-table td {
        background-color: #ffffff;
        text-align: center;
        padding: 0;
        height: 40px;
        border-right: 1px solid #f1f5f9;
        border-bottom: 1px solid #f1f5f9;
        position: relative;
    }
    .planning-table td.app-name {
        background-color: #f8fafc;
        color: #0f172a;
        font-weight: 600;
        text-align: left;
        padding-left: 15px;
        position: sticky;
        left: 0;
        z-index: 10;
        border-right: 2px solid #cbd5e1;
    }
    .planning-table td.weekend { background-color: #e2e8f0 !important; }
    .planning-table td.ferie { background-color: #FFE6F0 !important; color: #000; }
    
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

    /* TOOLTIP */
    .planning-table td:hover { z-index: 100; }
    .tooltip-content {
        visibility: hidden;
        width: 280px;
        background-color: #1e293b;
        color: #fff;
        text-align: left;
        border-radius: 6px;
        padding: 12px;
        position: absolute;
        bottom: 110%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.2s;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        font-size: 12px;
        line-height: 1.6;
        pointer-events: none;
        border: 1px solid #475569;
    }
    .tooltip-content::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: #1e293b transparent transparent transparent;
    }
    .planning-table td:hover .tooltip-content {
        visibility: visible;
        opacity: 1;
    }
    .tooltip-label {
        font-weight: bold;
        color: #4ade80;
        margin-right: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ==================================================
# 4. GÉNÉRATION PLANNING
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
            st.info("Aucune application configurée (Mode Admin requis).")
            continue

        # On utilise l'ordre défini par l'admin (la liste telle quelle)
        apps = st.session_state.apps

        html = '<div class="planning-wrap"><table class="planning-table">'
        
        # HEADER
        html += '<thead><tr><th class="app-header">Application</th>'
        for d in dates:
            day_letter = ["L", "M", "M", "J", "V", "S", "D"][d.weekday()]
            html += f'<th>{d.day}<br><small>{day_letter}</small></th>'
        html += '</tr></thead><tbody>'

        # BODY
        for app in apps:
            html += f'<tr><td class="app-name">{app}</td>'
            
            for d in dates:
                classes = []
                content = ""
                tooltip = ""
                
                # Weekend & Férié
                if d.weekday() >= 5: classes.append("weekend")
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
                    content = f'<div class="event-cell {type_cls}">{short_txt}</div>'
                    
                    duree = (found_ev['d2'] - found_ev['d1']).days + 1
                    tooltip = f"""
                    <div class="tooltip-content">
                        <span class="tooltip-label">📱 App:</span> {found_ev['app']}<br>
                        <span class="tooltip-label">🌐 Env:</span> {found_ev['env']}<br>
                        <span class="tooltip-label">🏷️ Type:</span> {found_ev['type']}<br>
                        <span class="tooltip-label">📅 Date:</span> {found_ev['d1'].strftime('%d/%m')} au {found_ev['d2'].strftime('%d/%m')}<br>
                        <span class="tooltip-label">⏱️ Durée:</span> {duree}j<br>
                        <span class="tooltip-label">💬 Note:</span> {found_ev['comment'] if found_ev['comment'] else '-'}
                    </div>
                    """

                td_cls = " ".join(classes)
                html += f'<td class="{td_cls}">{content}{tooltip}</td>'
            
            html += '</tr>'
        html += '</tbody></table></div>'
        
        st.markdown(html, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="display:flex; gap:15px; font-size:12px; margin-top:0px; color:#64748b;">
            <span><span style="color:#0070C0">■</span> MEP</span>
            <span><span style="color:#FF0000">■</span> INCIDENT</span>
            <span><span style="color:#FFC000">■</span> MAINTENANCE</span>
            <span><span style="color:#e2e8f0">■</span> Week-End</span>
            <span><span style="color:#FFE6F0">■</span> Férié</span>
        </div>
        """, unsafe_allow_html=True)

