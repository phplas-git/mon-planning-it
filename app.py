import streamlit as st
import pandas as pd
import calendar
from datetime import date, datetime
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
    if not supabase: return [], [], []
    try:
        # Charger Apps triées par 'ordre'
        res_apps = supabase.table("applications").select("*").order("ordre", desc=False).execute()
        apps_full = res_apps.data
        apps_names = [row['nom'] for row in apps_full]
        
        # Charger Events
        res_evts = supabase.table("evenements").select("*").execute()
        evts_data = res_evts.data
        for ev in evts_data:
            ev['d1'] = pd.to_datetime(ev['d1']).date()
            ev['d2'] = pd.to_datetime(ev['d2']).date()
            if 'h1' not in ev or not ev['h1']: ev['h1'] = "00:00"
            if 'h2' not in ev or not ev['h2']: ev['h2'] = "23:59"
            
        return apps_names, apps_full, evts_data
    except Exception as e:
        st.error(f"Erreur lecture : {e}")
        return [], [], []

def save_apps_db(df_apps):
    if not supabase: return
    try:
        supabase.table("applications").delete().neq("id", 0).execute()
        data = [{"nom": str(row['Nom']).upper().strip(), "ordre": int(row['Ordre'])} for _, row in df_apps.iterrows() if row['Nom']]
        if data: supabase.table("applications").insert(data).execute()
    except Exception as e: st.error(f"Erreur Apps : {e}")

def save_events_db(event_list):
    if not supabase: return
    try:
        supabase.table("evenements").delete().neq("id", 0).execute()
        if event_list:
            data = [{
                "app": ev['app'], "env": ev['env'], "type": ev['type'],
                "d1": pd.to_datetime(ev['d1']).strftime('%Y-%m-%d'),
                "d2": pd.to_datetime(ev['d2']).strftime('%Y-%m-%d'),
                "h1": ev.get('h1', '00:00'), "h2": ev.get('h2', '23:59'),
                "comment": str(ev['comment']) if ev['comment'] else ""
            } for ev in event_list]
            supabase.table("evenements").insert(data).execute()
    except Exception as e: st.error(f"Erreur Events : {e}")

# Variables Globales
TODAY = date.today()
JOURS_FERIES_2026 = [
    date(2026, 1, 1), date(2026, 4, 6), date(2026, 5, 1), date(2026, 5, 8),
    date(2026, 5, 14), date(2026, 5, 25), date(2026, 7, 14), date(2026, 8, 15),
    date(2026, 11, 1), date(2026, 11, 11), date(2026, 12, 25),
]

# Initialisation du State
if "data_loaded" not in st.session_state:
    an, af, ed = load_data()
    st.session_state.apps, st.session_state.apps_data, st.session_state.events = an, af, ed
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
    
    /* COLONNE APPS FIXE */
    .planning-table th.app-header { text-align: left; padding-left: 15px; width: 150px; position: sticky; left: 0; z-index: 30; background-color: #f1f5f9 !important; border-right: 2px solid #cbd5e1; }
    .planning-table td.app-name { background-color: #f8fafc !important; color: #0f172a !important; font-weight: 600; text-align: left; padding-left: 15px; position: sticky; left: 0; z-index: 20; border-right: 2px solid #cbd5e1; }
    
    /* AUJOURD'HUI */
    .today-col { background-color: #eff6ff !important; border-left: 1px solid #3b82f6 !important; border-right: 1px solid #3b82f6 !important; }
    th.today-header { background-color: #3b82f6 !important; color: white !important; }

    .planning-table td { text-align: center; padding: 0; height: 40px; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; position: relative; background-color: #ffffff; }
    .planning-table td.weekend { background-color: #e2e8f0 !important; }
    .planning-table td.ferie { background-color: #FFE6F0 !important; }
    
    .event-cell { display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; color: white; font-weight: bold; font-size: 10px; }
    .mep { background-color: #0070C0; } .inc { background-color: #FF0000; } .mai { background-color: #FFC000; color: black; } .test { background-color: #00B050; } .mor { background-color: #9600C8; }
    
    .planning-table td:hover { z-index: 100; background-color: #f1f5f9; }
    .tooltip-content { visibility: hidden; width: 280px; background-color: #1e293b; color: #fff; text-align: left; border-radius: 6px; padding: 12px; position: absolute; top: 100%; left: 50%; transform: translateX(-50%); opacity: 0; transition: opacity 0.2s; box-shadow: 0 10px 15px rgba(0,0,0,0.3); font-size: 12px; line-height: 1.6; z-index: 1000; pointer-events: none; border: 1px solid #475569; }
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
    if st.button("📅 Voir le Planning", use_container_width=True): st.session_state.page = "planning"; st.rerun()
    if st.button("📝 Gérer Événements", use_container_width=True): st.session_state.page = "events"; st.rerun()
    if st.button("📱 Gérer Applications", use_container_width=True): st.session_state.page = "apps"; st.rerun()
    st.divider()
    if st.button("🔄 Recharger depuis Cloud"): del st.session_state.data_loaded; st.rerun()

# ==================================================
# 4. PAGES
# ==================================================

# --- GESTION APPS ---
if st.session_state.page == "apps":
    st.title("📱 Gestion des Applications")
    clean_data = [{"Nom": i.get('nom', ''), "Ordre": i.get('ordre', 0)} for i in st.session_state.apps_data]
    df_apps = pd.DataFrame(clean_data if clean_data else columns=["Nom", "Ordre"])
    
    edited_apps = st.data_editor(df_apps, num_rows="dynamic", use_container_width=True, hide_index=True, 
                                 column_config={"Nom": st.column_config.TextColumn("Nom", required=True), 
                                                "Ordre": st.column_config.NumberColumn("Ordre", min_value=0, step=1, format="%d")}, key="ed_apps")
    if st.button("💾 Sauvegarder et Trier"):
        save_apps_db(edited_apps.sort_values(by="Ordre"))
        del st.session_state.data_loaded; st.success("Applications mises à jour !"); time.sleep(1); st.rerun()

# --- GESTION EVENTS ---
elif st.session_state.page == "events":
    st.title("📝 Gestion des Événements")
    if not st.session_state.apps: st.warning("Créez des apps d'abord.")
    else:
        if st.session_state.events:
            df_evts = pd.DataFrame(st.session_state.events)
            if not df_evts.empty:
                df_evts["d1"], df_evts["d2"] = pd.to_datetime(df_evts["d1"]).dt.date, pd.to_datetime(df_evts["d2"]).dt.date
        else:
            df_evts = pd.DataFrame(columns=["app", "env", "type", "d1", "d2", "h1", "h2", "comment"])

        col_config = {
            "app": st.column_config.SelectboxColumn("App", options=st.session_state.apps, required=True),
            "env": st.column_config.SelectboxColumn("Env", options=["PROD", "PRÉPROD", "RECETTE"], required=True),
            "type": st.column_config.SelectboxColumn("Type", options=["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"], required=True),
            "d1": st.column_config.DateColumn("Début", required=True),
            "d2": st.column_config.DateColumn("Fin", required=True),
            "h1": st.column_config.TextColumn("H. Début", default="00:00"),
            "h2": st.column_config.TextColumn("H. Fin", default="23:59"),
        }

        edited_evts = st.data_editor(df_evts, num_rows="dynamic", use_container_width=True, hide_index=True, column_config=col_config, key="ed_evts")
        
        if st.button("💾 Sauvegarder"):
            with st.spinner("Enregistrement..."):
                cleaned = []
                for _, r in edited_evts.iterrows():
                    if pd.notnull(r["app"]) and pd.notnull(r["d1"]):
                        d2_val = r["d2"] if pd.notnull(r["d2"]) else r["d1"]
                        h1_val = r["h1"] if (pd.notnull(r["h1"]) and str(r["h1"]).strip() != "") else "00:00"
                        h2_val = r["h2"] if (pd.notnull(r["h2"]) and str(r["h2"]).strip() != "") else "23:59"
                        cleaned.append({
                            "app": r["app"], "env": r["env"], "type": r["type"], 
                            "d1": r["d1"], "d2": d2_val, "h1": h1_val, "h2": h2_val,
                            "comment": r["comment"] if pd.notnull(r["comment"]) else ""
                        })
                save_events_db(cleaned)
                st.session_state.events = cleaned; st.success("OK"); time.sleep(1); st.rerun()

# --- PLANNING VISUEL ---
elif st.session_state.page == "planning":
    st.title("📅 Planning IT 2026")
    env_sel = st.radio("Secteur :", ["PROD", "PRÉPROD", "RECETTE"], horizontal=True)
    tabs = st.tabs(["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"])

    for i, tab in enumerate(tabs):
        with tab:
            m = i + 1
            days = calendar.monthrange(2026, m)[1]
            dates = [date(2026, m, d) for d in range(1, days + 1)]
            if not st.session_state.apps: st.info("Aucune donnée."); continue

            html = '<div class="planning-wrap"><table class="planning-table"><thead><tr><th class="app-header">Application</th>'
            for d in dates:
                th_cls = "today-header" if d == TODAY else ""
                html += f'<th class="{th_cls}">{d.day}<br><small>{["L","M","M","J","V","S","D"][d.weekday()]}</small></th>'
            html += '</tr></thead><tbody>'

            for app in st.session_state.apps:
                html += f'<tr><td class="app-name">{app}</td>'
                for d in dates:
                    cls, cnt, ttp = [], "", ""
                    if d == TODAY: cls.append("today-col")
                    if d.weekday() >= 5: cls.append("weekend")
                    if d in JOURS_FERIES_2026: cls.append("ferie"); cnt = "🎉"
                    
                    found = next((e for e in st.session_state.events if e["app"] == app and e["env"] == env_sel and e["d1"] <= d <= e["d2"]), None)
                    if found:
                        t_cls = found["type"][:3].lower() if found["type"] != "MAINTENANCE" else "mai"
                        if found["type"] == "TEST": t_cls = "test"
                        cnt = f'<div class="event-cell {t_cls}">{found["type"][:3].upper()}</div>'
                        ttp = f"""<div class="tooltip-content">
                            <span class="tooltip-label">📱 App:</span>{found["app"]}<br>
                            <span class="tooltip-label">🕒 Heures:</span>De {found.get('h1','00:00')} à {found.get('h2','23:59')}<br>
                            <span class="tooltip-label">📅 Dates:</span>{found["d1"].strftime("%d/%m")} au {found["d2"].strftime("%d/%m")}<br>
                            <span class="tooltip-label">💬 Note:</span>{found["comment"] if found["comment"] else "-"}
                        </div>"""
                    
                    html += f'<td class="{" ".join(cls)}">{cnt}{ttp}</td>'
                html += '</tr>'
            st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)
