import streamlit as st
import pandas as pd
import calendar
from datetime import date
from supabase import create_client, Client

# ==================================================
# 1. CONFIGURATION & CONNEXION DB
# ==================================================
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# Connexion Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_connection()

# --- FONCTIONS CRUD (Create, Read, Delete) ---

def load_data():
    """Charge les données depuis Supabase"""
    # 1. Charger Apps
    response_apps = supabase.table("applications").select("*").execute()
    apps_data = [row['nom'] for row in response_apps.data]
    
    # 2. Charger Events
    response_evts = supabase.table("evenements").select("*").execute()
    evts_data = response_evts.data
    
    # Conversion des strings dates en objets dates Python
    for ev in evts_data:
        ev['d1'] = pd.to_datetime(ev['d1']).date()
        ev['d2'] = pd.to_datetime(ev['d2']).date()
        
    return sorted(apps_data), evts_data

def save_apps_db(app_list):
    """Sauvegarde la liste des apps (Méthode Bulldozer)"""
    if not supabase: return
    try:
        # 1. NETTOYAGE ROBUSTE
        # On demande de supprimer toutes les lignes où l'ID n'est pas égal à 0.
        # Comme les IDs commencent à 1, cela vide toute la table d'un coup.
        supabase.table("applications").delete().neq("id", 0).execute()
        
        # 2. INSERTION
        if app_list:
            data_to_insert = [{"nom": name} for name in app_list]
            supabase.table("applications").insert(data_to_insert).execute()
            
    except Exception as e:
        st.error(f"❌ Erreur critique lors de la sauvegarde : {e}")

def save_events_db(event_list):
    """Pareil pour les événements"""
    current = supabase.table("evenements").select("id").execute()
    if current.data:
        ids = [x['id'] for x in current.data]
        supabase.table("evenements").delete().in_("id", ids).execute()
        
    if event_list:
        # Supabase veut des strings pour les dates (ISO format)
        data_to_insert = []
        for ev in event_list:
            data_to_insert.append({
                "app": ev['app'],
                "env": ev['env'],
                "type": ev['type'],
                "d1": ev['d1'].isoformat(),
                "d2": ev['d2'].isoformat(),
                "comment": ev['comment']
            })
        supabase.table("evenements").insert(data_to_insert).execute()


# Jours fériés
JOURS_FERIES_2026 = [
    date(2026, 1, 1), date(2026, 4, 6), date(2026, 5, 1), date(2026, 5, 8),
    date(2026, 5, 14), date(2026, 5, 25), date(2026, 7, 14), date(2026, 8, 15),
    date(2026, 11, 1), date(2026, 11, 11), date(2026, 12, 25),
]

# Initialisation du State (Chargement DB)
if "data_loaded" not in st.session_state:
    apps_db, evts_db = load_data()
    st.session_state.apps = apps_db
    st.session_state.events = evts_db
    st.session_state.data_loaded = True
    
if "page" not in st.session_state: st.session_state.page = "planning"
if "admin_unlocked" not in st.session_state: st.session_state.admin_unlocked = False

# ==================================================
# 2. CSS
# ==================================================
st.markdown("""
<style>
    /* Planning Table */
    .planning-wrap { overflow-x: auto; padding-bottom: 120px; margin-bottom: 20px; }
    .planning-table { width: 100%; border-collapse: separate; border-spacing: 0; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; font-family: 'Segoe UI', sans-serif; font-size: 13px; table-layout: fixed; }
    .planning-table th { background-color: #f8fafc; color: #334155; padding: 10px 5px; text-align: center; border-right: 1px solid #e2e8f0; border-bottom: 2px solid #cbd5e1; font-weight: 600; font-size: 11px; }
    .planning-table th.app-header { text-align: left; padding-left: 15px; width: 150px; position: sticky; left: 0; z-index: 20; background-color: #f8fafc; border-right: 2px solid #cbd5e1; }
    .planning-table td { background-color: #ffffff; text-align: center; padding: 0; height: 40px; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; position: relative; }
    .planning-table td.app-name { background-color: #f8fafc; color: #0f172a; font-weight: 600; text-align: left; padding-left: 15px; position: sticky; left: 0; z-index: 10; border-right: 2px solid #cbd5e1; }
    .planning-table td.weekend { background-color: #e2e8f0 !important; }
    .planning-table td.ferie { background-color: #FFE6F0 !important; color: #000; }
    
    /* Events */
    .event-cell { display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; color: white; font-weight: bold; font-size: 10px; }
    .mep { background-color: #0070C0; }
    .inc { background-color: #FF0000; }
    .mai { background-color: #FFC000; color: black; }
    .test { background-color: #00B050; }
    .mor { background-color: #9600C8; }

    /* Tooltip */
    .planning-table td:hover { z-index: 100; }
    .tooltip-content { visibility: hidden; width: 280px; background-color: #1e293b; color: #fff; text-align: left; border-radius: 6px; padding: 12px; position: absolute; top: 100%; left: 50%; transform: translateX(-50%); opacity: 0; transition: opacity 0.2s; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); font-size: 12px; line-height: 1.6; pointer-events: none; border: 1px solid #475569; }
    .tooltip-content::after { content: ""; position: absolute; bottom: 100%; left: 50%; margin-left: -5px; border-width: 5px; border-style: solid; border-color: transparent transparent #1e293b transparent; }
    .planning-table td:hover .tooltip-content { visibility: visible; opacity: 1; }
    .tooltip-label { font-weight: bold; color: #4ade80; margin-right: 5px; }
</style>
""", unsafe_allow_html=True)

# ==================================================
# 3. SIDEBAR
# ==================================================
with st.sidebar:
    st.title("📌 Menu")
    
    if st.button("📅 Voir le Planning", use_container_width=True):
        st.session_state.page = "planning"
        st.rerun()
        
    if st.button("📝 Gérer Événements", use_container_width=True):
        st.session_state.page = "events"
        st.rerun()

    st.divider()

    st.subheader("🛡️ Administration")
    mode_admin = st.toggle("Mode Admin", key="toggle_admin")
    
    if mode_admin:
        if not st.session_state.admin_unlocked:
            pwd = st.text_input("Mot de passe", type="password")
            if pwd == "admin123":
                st.session_state.admin_unlocked = True
                st.rerun()
            elif pwd:
                st.error("Incorrect")
        
        if st.session_state.admin_unlocked:
            st.success("🔓 Admin Connecté")
            if st.button("📱 Gérer Applications", use_container_width=True, type="primary"):
                st.session_state.page = "apps"
                st.rerun()
    else:
        st.session_state.admin_unlocked = False
            
    st.divider()
    if st.button("🔄 Recharger (DB)"):
        # Force le rechargement depuis la DB
        del st.session_state.data_loaded
        st.rerun()

# ==================================================
# 4. CONTENU
# ==================================================

# --- GESTION APPS ---
if st.session_state.page == "apps":
    if not st.session_state.admin_unlocked:
        st.error("⛔ Accès refusé.")
    else:
        st.title("📱 Gestion des Applications (Base de Données)")
        st.info("Les modifications sont enregistrées dans le Cloud.")
        
        df_apps = pd.DataFrame(st.session_state.apps, columns=["Nom Application"])
        
        edited_apps = st.data_editor(
            df_apps, num_rows="dynamic", use_container_width=True, hide_index=True, key="editor_apps"
        )
        
        if st.button("💾 Sauvegarder dans la Base de Données"):
            new_list = [x.upper().strip() for x in edited_apps["Nom Application"].tolist() if x]
            # Mise à jour State
            st.session_state.apps = new_list
            # Mise à jour DB
            save_apps_db(new_list)
            st.success("✅ Base de données mise à jour avec succès !")

# --- GESTION EVENTS ---
elif st.session_state.page == "events":
    st.title("📝 Gestion des Événements")
    
    if not st.session_state.apps:
        st.warning("⚠️ Aucune application. Ajoutez-en d'abord.")
    else:
        st.caption("Modifiez le tableau et cliquez sur Sauvegarder.")
        
        if st.session_state.events:
            df_evts = pd.DataFrame(st.session_state.events)
            # Conversion dates pour l'éditeur
            if not df_evts.empty:
                df_evts["d1"] = pd.to_datetime(df_evts["d1"]).dt.date
                df_evts["d2"] = pd.to_datetime(df_evts["d2"]).dt.date
        else:
            df_evts = pd.DataFrame(columns=["app", "env", "type", "d1", "d2", "comment"])

        col_config = {
            "app": st.column_config.SelectboxColumn("Application", options=st.session_state.apps, required=True),
            "env": st.column_config.SelectboxColumn("Env", options=["PROD", "PRÉPROD", "RECETTE"], required=True),
            "type": st.column_config.SelectboxColumn("Type", options=["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"], required=True),
            "d1": st.column_config.DateColumn("Début", required=True),
            "d2": st.column_config.DateColumn("Fin", required=True),
            "comment": st.column_config.TextColumn("Détails")
        }

        edited_evts = st.data_editor(
            df_evts, num_rows="dynamic", use_container_width=True, column_config=col_config, hide_index=True, key="editor_events"
        )

        if st.button("💾 Sauvegarder dans la Base de Données"):
            cleaned = []
            for _, row in edited_evts.iterrows():
                if row["app"] and row["d1"] and row["d2"]:
                    cleaned.append({
                        "app": row["app"], "env": row["env"], "type": row["type"],
                        "d1": row["d1"], "d2": row["d2"], "comment": row["comment"]
                    })
            # Mise à jour State
            st.session_state.events = cleaned
            # Mise à jour DB
            save_events_db(cleaned)
            st.success("✅ Événements sauvegardés dans le Cloud !")

# --- PLANNING VISUEL ---
elif st.session_state.page == "planning":
    st.title("📅 Planning Visuel 2026")
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
                st.info("Aucune donnée.")
                continue

            apps = st.session_state.apps

            html = '<div class="planning-wrap"><table class="planning-table">'
            html += '<thead><tr><th class="app-header">Application</th>'
            for d in dates:
                day_letter = ["L", "M", "M", "J", "V", "S", "D"][d.weekday()]
                html += f'<th>{d.day}<br><small>{day_letter}</small></th>'
            html += '</tr></thead><tbody>'

            for app in apps:
                html += f'<tr><td class="app-name">{app}</td>'
                for d in dates:
                    classes = []
                    content = ""
                    tooltip = ""
                    
                    if d.weekday() >= 5: classes.append("weekend")
                    if d in JOURS_FERIES_2026:
                        classes.append("ferie")
                        if not content: content = "🎉"

                    found_ev = None
                    for ev in st.session_state.events:
                        if ev["app"] == app and ev["env"] == env_selected:
                            # Sécurisation date
                            ev_d1 = ev["d1"] if isinstance(ev["d1"], date) else pd.to_datetime(ev["d1"]).date()
                            ev_d2 = ev["d2"] if isinstance(ev["d2"], date) else pd.to_datetime(ev["d2"]).date()
                            
                            if ev_d1 <= d <= ev_d2:
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
                        
                        ev_d1 = found_ev["d1"] if isinstance(found_ev["d1"], date) else pd.to_datetime(found_ev["d1"]).date()
                        ev_d2 = found_ev["d2"] if isinstance(found_ev["d2"], date) else pd.to_datetime(found_ev["d2"]).date()
                        duree = (ev_d2 - ev_d1).days + 1
                        
                        tooltip = f"""
                        <div class="tooltip-content">
                            <span class="tooltip-label">📱 App:</span> {found_ev['app']}<br>
                            <span class="tooltip-label">🌐 Env:</span> {found_ev['env']}<br>
                            <span class="tooltip-label">🏷️ Type:</span> {found_ev['type']}<br>
                            <span class="tooltip-label">📅 Date:</span> {ev_d1.strftime('%d/%m')} au {ev_d2.strftime('%d/%m')}<br>
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

