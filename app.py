import streamlit as st
import pandas as pd
import calendar
from datetime import date
from supabase import create_client, Client
import time

# ==================================================
# 1. CONFIGURATION & CONNEXION DB
# ==================================================
st.set_page_config(page_title="Planning IT Pro", layout="wide")

@st.cache_resource
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Erreur connexion Supabase : {e}")
        return None

supabase = init_connection()

# --- FONCTIONS CRUD ---

def load_data():
    """Charge les données (Apps triées par ordre + Events)"""
    if not supabase: return [], [], []
    try:
        # 1. Charger Apps triées
        response_apps = supabase.table("applications").select("*").order("ordre", desc=False).execute()
        apps_full = response_apps.data
        apps_names = [row['nom'] for row in apps_full]
        
        # 2. Charger Events
        response_evts = supabase.table("evenements").select("*").execute()
        evts_data = response_evts.data
        for ev in evts_data:
            ev['d1'] = pd.to_datetime(ev['d1']).date()
            ev['d2'] = pd.to_datetime(ev['d2']).date()
            
        return apps_names, apps_full, evts_data
    except Exception as e:
        st.error(f"Erreur lecture données : {e}")
        return [], [], []

def save_apps_db(df_apps):
    """Sauvegarde Apps avec leur ordre (Bulldozer)"""
    if not supabase: return
    try:
        supabase.table("applications").delete().neq("id", 0).execute()
        data_to_insert = []
        for _, row in df_apps.iterrows():
            if row['Nom']:
                data_to_insert.append({"nom": str(row['Nom']).upper().strip(), "ordre": int(row['Ordre'])})
        if data_to_insert:
            supabase.table("applications").insert(data_to_insert).execute()
    except Exception as e:
        st.error(f"❌ Erreur sauvegarde Apps : {e}")

def save_events_db(event_list):
    """Sauvegarde Events (Version Robuste)"""
    if not supabase: return
    try:
        supabase.table("evenements").delete().neq("id", 0).execute()
        if event_list:
            data = []
            for ev in event_list:
                data.append({
                    "app": ev['app'],
                    "env": ev['env'],
                    "type": ev['type'],
                    "d1": pd.to_datetime(ev['d1']).strftime('%Y-%m-%d'),
                    "d2": pd.to_datetime(ev['d2']).strftime('%Y-%m-%d'),
                    "comment": str(ev['comment']) if ev['comment'] else ""
                })
            supabase.table("evenements").insert(data).execute()
    except Exception as e:
        st.error(f"❌ Erreur sauvegarde Events : {e}")

# Jours fériés 2026
JOURS_FERIES_2026 = [
    date(2026, 1, 1), date(2026, 4, 6), date(2026, 5, 1), date(2026, 5, 8),
    date(2026, 5, 14), date(2026, 5, 25), date(2026, 7, 14), date(2026, 8, 15),
    date(2026, 11, 1), date(2026, 11, 11), date(2026, 12, 25),
]

# State Management
if "data_loaded" not in st.session_state:
    with st.spinner("Synchronisation Cloud..."):
        an, af, ed = load_data()
        st.session_state.apps = an
        st.session_state.apps_data = af
        st.session_state.events = ed
        st.session_state.data_loaded = True
if "page" not in st.session_state: st.session_state.page = "planning"

# ==================================================
# 2. CSS DESIGN
# ==================================================
st.markdown("""
<style>
    .planning-wrap { overflow-x: auto; padding-bottom: 120px; }
    .planning-table { width: 100%; border-collapse: separate; border-spacing: 0; background-color: #fff; border: 1px solid #e2e8f0; border-radius: 8px; font-family: sans-serif; font-size: 13px; table-layout: fixed; }
    .planning-table th { background-color: #f8fafc; color: #334155; padding: 10px 5px; text-align: center; border-right: 1px solid #e2e8f0; border-bottom: 2px solid #cbd5e1; font-size: 11px; }
    .planning-table th.app-header { text-align: left; padding-left: 15px; width: 150px; position: sticky; left: 0; z-index: 20; background-color: #f8fafc; border-right: 2px solid #cbd5e1; }
    .planning-table td { text-align: center; padding: 0; height: 40px; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; position: relative; }
    .planning-table td.app-name { background-color: #f8fafc; font-weight: 600; text-align: left; padding-left: 15px; position: sticky; left: 0; z-index: 10; border-right: 2px solid #cbd5e1; }
    .planning-table td.weekend { background-color: #e2e8f0 !important; }
    .planning-table td.ferie { background-color: #FFE6F0 !important; }
    .event-cell { display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; color: white; font-weight: bold; font-size: 10px; }
    .mep { background-color: #0070C0; } .inc { background-color: #FF0000; } .mai { background-color: #FFC000; color: black; } .test { background-color: #00B050; } .mor { background-color: #9600C8; }
    .planning-table td:hover { z-index: 100; background-color: #f1f5f9; }
    .tooltip-content { visibility: hidden; width: 280px; background-color: #1e293b; color: #fff; text-align: left; border-radius: 6px; padding: 12px; position: absolute; top: 100%; left: 50%; transform: translateX(-50%); opacity: 0; transition: opacity 0.2s; box-shadow: 0 10px 15px rgba(0,0,0,0.3); font-size: 12px; line-height: 1.6; pointer-events: none; border: 1px solid #475569; }
    .tooltip-content::after { content: ""; position: absolute; bottom: 100%; left: 50%; margin-left: -5px; border-width: 5px; border-style: solid; border-color: transparent transparent #1e293b transparent; }
    .planning-table td:hover .tooltip-content { visibility: visible; opacity: 1; }
    .tooltip-label { font-weight: bold; color: #4ade80; margin-right: 5px; }
</style>
""", unsafe_allow_html=True)

# ==================================================
# 3. SIDEBAR (NAVIGATION)
# ==================================================
with st.sidebar:
    st.title("📌 Menu")
    if st.button("📅 Voir le Planning", use_container_width=True): st.session_state.page = "planning"; st.rerun()
    if st.button("📝 Gérer Événements", use_container_width=True): st.session_state.page = "events"; st.rerun()
    if st.button("📱 Gérer Applications", use_container_width=True): st.session_state.page = "apps"; st.rerun()
    st.divider()
    if st.button("🔄 Recharger depuis Cloud"): 
        if "data_loaded" in st.session_state: del st.session_state.data_loaded
        st.rerun()

# ==================================================
# 4. PAGES
# ==================================================

# --- PAGE APPS ---
if st.session_state.page == "apps":
    st.title("📱 Gestion des Applications")
    
    clean_data = [{"Nom": i.get('nom', ''), "Ordre": i.get('ordre', 0)} for i in st.session_state.apps_data]
    if clean_data:
        df_apps = pd.DataFrame(clean_data)
    else:
        df_apps = pd.DataFrame(columns=["Nom", "Ordre"])
    
    edited_apps = st.data_editor(df_apps, num_rows="dynamic", use_container_width=True, hide_index=True, 
                                 column_config={
                                     "Nom": st.column_config.TextColumn("Nom", required=True), 
                                     "Ordre": st.column_config.NumberColumn("Ordre", min_value=0, step=1, format="%d")
                                 }, key="ed_apps")
                                 
    if st.button("💾 Sauvegarder et Trier"):
        save_apps_db(edited_apps.sort_values(by="Ordre"))
        if "data_loaded" in st.session_state: del st.session_state.data_loaded
        st.success("Applications mises à jour !"); time.sleep(1); st.rerun()

# --- PAGE EVENTS ---
elif st.session_state.page == "events":
    st.title("📝 Gestion des Événements")
    if not st.session_state.apps:
        st.warning("Créez des applications d'abord.")
    else:
        # Correction de la syntaxe DataFrame vide
        if st.session_state.events:
            df_evts = pd.DataFrame(st.session_state.events)
            if not df_evts.empty:
                df_evts["d1"] = pd.to_datetime(df_evts["d1"]).dt.date
                df_evts["d2"] = pd.to_datetime(df_evts["d2"]).dt.date
        else:
            df_evts = pd.DataFrame(columns=["app", "env", "type", "d1", "d2", "comment"])

        edited_evts = st.data_editor(df_evts, num_rows="dynamic", use_container_width=True, hide_index=True,
                                     column_config={
                                         "app": st.column_config.SelectboxColumn("App", options=st.session_state.apps, required=True),
                                         "env": st.column_config.SelectboxColumn("Env", options=["PROD", "PRÉPROD", "RECETTE"], required=True),
                                         "type": st.column_config.SelectboxColumn("Type", options=["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"], required=True),
                                         "d1": st.column_config.DateColumn("Début", required=True),
                                         "d2": st.column_config.DateColumn("Fin", required=True),
                                         "comment": st.column_config.TextColumn("Commentaire")
                                     }, key="ed_evts")
                                     
        if st.button("💾 Sauvegarder (Cloud)"):
            cleaned = []
            for _, r in edited_evts.iterrows():
                # Vérification que les colonnes obligatoires ne sont pas vides
                if pd.notnull(r["app"]) and pd.notnull(r["d1"]):
                    cleaned.append({
                        "app": r["app"], 
                        "env": r["env"], 
                        "type": r["type"], 
                        "d1": r["d1"], 
                        "d2": r["d2"], 
                        "comment": r["comment"]
                    })
            save_events_db(cleaned)
            st.session_state.events = cleaned
            st.success("Événements sauvegardés !"); time.sleep(1); st.rerun()

# --- PAGE PLANNING ---
elif st.session_state.page == "planning":
    st.title("📅 Planning Visuel 2026")
    env_sel = st.radio("Secteur :", ["PROD", "PRÉPROD", "RECETTE"], horizontal=True)
    months = ["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
    tabs = st.tabs(months)

    for i, tab in enumerate(tabs):
        with tab:
            m = i + 1
            days = calendar.monthrange(2026, m)[1]
            dates = [date(2026, m, d) for d in range(1, days + 1)]
            if not st.session_state.apps: st.info("Aucune donnée."); continue

            html = '<div class="planning-wrap"><table class="planning-table"><thead><tr><th class="app-header">Application</th>'
            for d in dates: html += f'<th>{d.day}<br><small>{["L","M","M","J","V","S","D"][d.weekday()]}</small></th>'
            html += '</tr></thead><tbody>'

            for app in st.session_state.apps:
                html += f'<tr><td class="app-name">{app}</td>'
                for d in dates:
                    cls, cnt, ttp = [], "", ""
                    if d.weekday() >= 5: cls.append("weekend")
                    if d in JOURS_FERIES_2026: cls.append("ferie"); cnt = "🎉"
                    
                    found = next((e for e in st.session_state.events if e["app"] == app and e["env"] == env_sel and e["d1"] <= d <= e["d2"]), None)
                    if found:
                        t_cls = found["type"][:3].lower() if found["type"] != "MAINTENANCE" else "mai"
                        if found["type"] == "TEST": t_cls = "test"
                        cnt = f'<div class="event-cell {t_cls}">{found["type"][:3].upper()}</div>'
                        ttp = f'<div class="tooltip-content"><span class="tooltip-label">📱 App:</span>{found["app"]}<br><span class="tooltip-label">🏷️ Type:</span>{found["type"]}<br><span class="tooltip-label">📅 Dates:</span>{found["d1"].strftime("%d/%m")} au {found["d2"].strftime("%d/%m")}<br><span class="tooltip-label">💬 Note:</span>{found["comment"] if found["comment"] else "-"}</div>'
                    
                    html += f'<td class="{" ".join(cls)}">{cnt}{ttp}</td>'
                html += '</tr>'
            st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)
