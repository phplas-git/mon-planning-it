import streamlit as st
import pandas as pd
import calendar
from datetime import date, datetime
from supabase import create_client, Client
import time
import holidays

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
        res_apps = supabase.table("applications").select("*").order("ordre", desc=False).execute()
        apps_full = res_apps.data
        apps_names = [row['nom'] for row in apps_full]
        
        res_evts = supabase.table("evenements").select("*").execute()
        evts_data = res_evts.data
        for ev in evts_data:
            ev['d1'] = pd.to_datetime(ev['d1']).date()
            ev['d2'] = pd.to_datetime(ev['d2']).date()
            if 'h1' not in ev: ev['h1'] = "00:00"
            if 'h2' not in ev: ev['h2'] = "23:59"
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

# --- VARIABLES TEMPORELLES ---
TODAY = date.today()
MONTHS_FR = ["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]

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
    .planning-wrap { overflow-x: auto; padding-bottom: 150px; }
    .planning-table { width: 100%; border-collapse: separate; border-spacing: 0; background-color: #fff; border: 1px solid #e2e8f0; border-radius: 8px; font-family: sans-serif; font-size: 12px; table-layout: fixed; }
    .planning-table th { background-color: #f8fafc; color: #334155; padding: 10px 2px; text-align: center; border-right: 1px solid #e2e8f0; border-bottom: 2px solid #cbd5e1; }
    .planning-table th.app-header { text-align: left; padding-left: 15px; width: 150px; position: sticky; left: 0; z-index: 30; background-color: #f1f5f9 !important; border-right: 2px solid #cbd5e1; }
    .planning-table td.app-name { background-color: #f8fafc !important; color: #0f172a !important; font-weight: 600; text-align: left; padding-left: 15px; position: sticky; left: 0; z-index: 20; border-right: 2px solid #cbd5e1; }
    .today-col { background-color: #eff6ff !important; border-left: 1px solid #3b82f6 !important; border-right: 1px solid #3b82f6 !important; }
    th.today-header { background-color: #3b82f6 !important; color: white !important; }
    .planning-table td { text-align: center; padding: 0; height: 38px; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; position: relative; }
    .planning-table td.weekend { background-color: #f1f5f9 !important; }
    .planning-table td.ferie { background-color: #FFE6F0 !important; }
    .event-cell { display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; color: white; font-weight: bold; font-size: 9px; line-height: 1; }
    .mep { background-color: #0070C0; } .inc { background-color: #FF0000; } .mai { background-color: #FFC000; color: black; } .test { background-color: #00B050; } .mor { background-color: #9600C8; }
    .planning-table td:hover { background-color: #f8fafc; z-index: 50; }
    .tooltip-content { visibility: hidden; width: 240px; background-color: #1e293b; color: #fff; text-align: left; border-radius: 6px; padding: 10px; position: absolute; bottom: 125%; left: 50%; transform: translateX(-50%); opacity: 0; transition: opacity 0.2s; box-shadow: 0 10px 15px rgba(0,0,0,0.3); font-size: 11px; z-index: 9999; pointer-events: none; border: 1px solid #475569; }
    .planning-table td:hover .tooltip-content { visibility: visible; opacity: 1; }
    .tooltip-label { font-weight: bold; color: #4ade80; }
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
    years = [2025, 2026, 2027, 2028]
    sel_year = st.selectbox("Année", years, index=years.index(TODAY.year))
    st.divider()
    if st.button("🔄 Actualiser"): del st.session_state.data_loaded; st.rerun()

# ==================================================
# 4. PAGES
# ==================================================

if st.session_state.page == "apps":
    st.title("📱 Gestion des Applications")
    clean_data = [{"Nom": i.get('nom', ''), "Ordre": i.get('ordre', 0)} for i in st.session_state.apps_data]
    df_apps = pd.DataFrame(clean_data if clean_data else None, columns=["Nom", "Ordre"])
    edited_apps = st.data_editor(df_apps, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_apps")
    if st.button("💾 Sauvegarder"):
        save_apps_db(edited_apps.sort_values(by="Ordre"))
        del st.session_state.data_loaded; st.rerun()

elif st.session_state.page == "events":
    st.title("📝 Gestion des Événements")
    if not st.session_state.apps: st.warning("Ajoutez des apps.")
    else:
        df_evts = pd.DataFrame(st.session_state.events if st.session_state.events else None)
        cols_to_show = ["app", "env", "type", "d1", "d2", "h1", "h2", "comment"]
        # On ne garde que les colonnes métier pour l'affichage
        display_df = df_evts[cols_to_show] if not df_evts.empty else pd.DataFrame(columns=cols_to_show)
        
        edited_evts = st.data_editor(display_df, num_rows="dynamic", use_container_width=True, hide_index=True, 
                                     column_config={"app": st.column_config.SelectboxColumn("App", options=st.session_state.apps),
                                                    "env": st.column_config.SelectboxColumn("Env", options=["PROD", "PRÉPROD", "RECETTE"]),
                                                    "type": st.column_config.SelectboxColumn("Type", options=["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"])}, key="ed_evts")
        if st.button("💾 Sauvegarder"):
            cleaned = []
            for _, r in edited_evts.iterrows():
                if pd.notnull(r["app"]) and pd.notnull(r["d1"]):
                    d2_val = r["d2"] if pd.notnull(r["d2"]) else r["d1"]
                    cleaned.append({"app": r["app"], "env": r["env"], "type": r["type"], "d1": r["d1"], "d2": d2_val, "h1": r.get("h1","00:00"), "h2": r.get("h2","23:59"), "comment": r.get("comment","")})
            save_events_db(cleaned); del st.session_state.data_loaded; st.rerun()

elif st.session_state.page == "planning":
    st.title(f"📅 Planning Visuel {sel_year}")
    env_sel = st.radio("Secteur :", ["PROD", "PRÉPROD", "RECETTE"], horizontal=True)
    fr_holidays = holidays.France(years=sel_year)
    
    tabs = st.tabs(MONTHS_FR)

    for i, tab in enumerate(tabs):
        with tab:
            m = i + 1
            days_in_month = calendar.monthrange(sel_year, m)[1]
            dates_m = [date(sel_year, m, d) for d in range(1, days_in_month + 1)]
            
            if not st.session_state.apps:
                st.info("Aucune application.")
                continue

            # CONSTRUCTION TABLEAU
            html = '<div class="planning-wrap"><table class="planning-table"><thead><tr><th class="app-header">Application</th>'
            for d in dates_m:
                th_cls = "today-header" if d == TODAY else ""
                html += f'<th class="{th_cls}">{d.day}<br>{["L","M","M","J","V","S","D"][d.weekday()]}</th>'
            html += '</tr></thead><tbody>'

            for app_n in st.session_state.apps:
                html += f'<tr><td class="app-name">{app_n}</td>'
                for d in dates_m:
                    cls, cnt, ttp = [], "", ""
                    if d == TODAY: cls.append("today-col")
                    if d.weekday() >= 5: cls.append("weekend")
                    
                    h_name = fr_holidays.get(d)
                    if h_name:
                        cls.append("ferie")
                        cnt = "🎉"

                    ev = next((e for e in st.session_state.events if e["app"] == app_n and e["env"] == env_sel and e["d1"] <= d <= e["d2"]), None)
                    if ev:
                        t_raw = str(ev["type"]).upper()
                        t_cls = "mep" if "MEP" in t_raw else "inc" if "INC" in t_raw else "mai" if "MAI" in t_raw else "test" if "TEST" in t_raw else "mor"
                        cnt = f'<div class="event-cell {t_cls}">{t_raw[:3]}</div>'
                        dur = (ev["d2"] - ev["d1"]).days + 1
                        
                        ttp = f"""<div class="tooltip-content">
                            <span class="tooltip-label">App:</span> {ev['app']}<br>
                            <span class="tooltip-label">🕒 Heures:</span> {ev.get('h1','00:00')} - {ev.get('h2','23:59')}<br>
                            <span class="tooltip-label">📅 Dates:</span> {ev['d1'].strftime('%d/%m')} au {ev['d2'].strftime('%d/%m')}<br>
                            <span class="tooltip-label">⏱️ Durée:</span> {dur} j<br>
                            {f"<span class='tooltip-label'>🎊 Férié:</span> {h_name}<br>" if h_name else ""}
                            <span class="tooltip-label">💬 Note:</span> {ev.get('comment','-')}
                        </div>"""
                    elif h_name:
                        ttp = f'<div class="tooltip-content"><span class="tooltip-label">🎊 Férié:</span> {h_name}</div>'
                    
                    html += f'<td class="{" ".join(cls)}">{cnt}{ttp}</td>'
                html += '</tr>'
            st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)
