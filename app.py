import streamlit as st
import pandas as pd
import calendar
from datetime import date, datetime
from supabase import create_client, Client
import time
import holidays
# Indicateur d'environnement
# On utilise .get() pour éviter que l'app plante si la clé n'existe pas encore
env_type = st.secrets["supabase"].get("env", "PRODUCTION")

if env_type == "DEVELOPPEMENT":
    st.sidebar.warning("⚠️ MODE DÉVELOPPEMENT")
    st.sidebar.caption("Base : Planning-IT-DEV")
# ==================================================
# 1. CONFIGURATION & CONNEXION DB
# ==================================================
st.set_page_config(
    page_title="Planning IT Pro", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

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
                "comment": str(ev['comment'])
            } for ev in event_list]
            supabase.table("evenements").insert(data).execute()
    except Exception as e: st.error(f"Erreur Events : {e}")

# --- VARIABLES ---
TODAY = date.today()
MONTHS_FR = ["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]

if "data_loaded" not in st.session_state:
    an, af, ed = load_data()
    st.session_state.apps, st.session_state.apps_data, st.session_state.events = an, af, ed
    st.session_state.data_loaded = True
if "page" not in st.session_state: st.session_state.page = "planning"

# ==================================================
# 2. CSS DESIGN (OPTIMISÉ AVEC SCROLL)
# ==================================================
st.markdown("""
<style>
    /* MASQUER LE MENU STREAMLIT */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Masquer le bouton "Deploy" et autres éléments du header */
    .stDeployButton {display: none;}
    button[kind="header"] {display: none;}
    
    /* Container avec scroll vertical et horizontal */
    .planning-wrap { 
        overflow: auto; 
        max-height: 70vh; 
        padding-bottom: 20px; 
        position: relative;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
    }
    
    .planning-table { 
        width: 100%; 
        border-collapse: separate; 
        border-spacing: 0; 
        background-color: #fff; 
        font-family: sans-serif; 
        font-size: 13px;
    }
    
    /* En-têtes STICKY (fixes au scroll vertical) */
    .planning-table thead {
        position: sticky;
        top: 0;
        z-index: 50;
    }
    
    .planning-table th { 
        background-color: #f8fafc; 
        color: #334155; 
        padding: 12px 4px; 
        text-align: center; 
        border-right: 1px solid #e2e8f0; 
        border-bottom: 2px solid #cbd5e1;
        font-weight: 600;
        white-space: nowrap;
    }
    
    /* Colonne Application STICKY (fixe au scroll horizontal) */
    .planning-table th.app-header { 
        text-align: left; 
        padding-left: 15px; 
        width: 150px;
        min-width: 150px;
        position: sticky; 
        left: 0; 
        z-index: 60; 
        background-color: #f1f5f9 !important; 
        border-right: 2px solid #cbd5e1;
        box-shadow: 2px 0 4px rgba(0,0,0,0.05);
    }
    
    .planning-table td.app-name { 
        background-color: #f8fafc !important; 
        color: #0f172a !important; 
        font-weight: 600; 
        text-align: left; 
        padding: 12px 15px;
        position: sticky; 
        left: 0; 
        z-index: 40; 
        border-right: 2px solid #cbd5e1;
        box-shadow: 2px 0 4px rgba(0,0,0,0.05);
    }
    
    /* Cellules normales */
    .planning-table td { 
        text-align: center; 
        padding: 0; 
        height: 42px;
        min-width: 35px;
        border-right: 1px solid #f1f5f9; 
        border-bottom: 1px solid #f1f5f9; 
        position: relative; 
        background-color: #ffffff; 
    }

    /* PRIORITÉS COULEURS - ORDRE IMPORTANT */
    .weekend { background-color: #f1f5f9 !important; }
    .ferie { background-color: #FFE6F0 !important; }
    
    /* Date du jour - SEULEMENT pour les cellules vides */
    .today-col:not(.has-tooltip) { 
        background-color: #eff6ff !important; 
        box-shadow: inset 0 0 0 2px #3b82f6 !important; 
    }
    
    /* En-tête du jour actuel */
    th.today-header { 
        background-color: #3b82f6 !important; 
        color: white !important; 
        font-weight: 700;
    }
    
    /* Les événements doivent rester avec leur couleur d'origine */
    .has-tooltip.today-col {
        background-color: transparent !important;
        box-shadow: none !important;
    }

    /* Événements */
    .event-cell { 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        width: 100%; 
        height: 100%; 
        color: white; 
        font-weight: bold; 
        font-size: 11px; 
        line-height: 1; 
        position: relative; 
        z-index: 5; 
        cursor: pointer; 
    }
    .mep { background-color: #0070C0; } 
    .inc { background-color: #FF0000; } 
    .mai { background-color: #FFC000; color: black; } 
    .test { background-color: #00B050; } 
    .tnr { background-color: #70AD47; }
    .mor { background-color: #9600C8; }
    
    /* TOOLTIP */
    .has-tooltip { position: relative; }
    
    /* Amélioration visuelle */
    .planning-table tbody tr:hover td:not(.app-name) {
        background-color: #fafafa;
    }
    
    /* Scroll bars personnalisées */
    .planning-wrap::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    .planning-wrap::-webkit-scrollbar-track {
        background: #f1f5f9;
    }
    .planning-wrap::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 5px;
    }
    .planning-wrap::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
    
    /* Tooltip simple avec CSS pur */
    .has-tooltip { position: relative; }
    .has-tooltip .tooltip-box {
        visibility: hidden;
        opacity: 0;
        width: 300px;
        background-color: #1e293b;
        color: #fff;
        border-radius: 6px;
        padding: 14px;
        position: absolute;
        z-index: 9999;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        margin-bottom: 8px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        font-size: 12px;
        text-align: left;
        line-height: 1.7;
        pointer-events: none;
        transition: opacity 0.2s, visibility 0.2s;
    }
    .has-tooltip .tooltip-box::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -6px;
        border-width: 6px;
        border-style: solid;
        border-color: #1e293b transparent transparent transparent;
    }
    .has-tooltip:hover .tooltip-box {
        visibility: visible;
        opacity: 1;
    }
    /* Ajustement si le tooltip dépasse en haut */
    tr:first-child .has-tooltip .tooltip-box {
        bottom: auto;
        top: 100%;
        margin-top: 8px;
        margin-bottom: 0;
    }
    tr:first-child .has-tooltip .tooltip-box::after {
        top: auto;
        bottom: 100%;
        border-color: transparent transparent #1e293b transparent;
    }
</style>
""", unsafe_allow_html=True)

# ==================================================
# 3. SIDEBAR
# ==================================================
with st.sidebar:
    st.title("📌 Menu")
    if st.button("📅 Planning", use_container_width=True): st.session_state.page = "planning"; st.rerun()
    if st.button("📝 Événements", use_container_width=True): st.session_state.page = "events"; st.rerun()
    if st.button("📱 Applications", use_container_width=True): st.session_state.page = "apps"; st.rerun()
    st.divider()
    years_list = [2025, 2026, 2027, 2028]
    sel_year = st.selectbox("Année", years_list, index=years_list.index(TODAY.year) if TODAY.year in years_list else 1)
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
    
    col1, col2 = st.columns([1, 4])
    with col1:
        save_btn = st.button("💾 Sauvegarder", type="primary", use_container_width=True)
    
    if save_btn:
        with st.spinner("Sauvegarde en cours..."):
            save_apps_db(edited_apps.sort_values(by="Ordre"))
            st.success("✅ Applications sauvegardées avec succès !")
            time.sleep(1)
            del st.session_state.data_loaded
            st.rerun()

elif st.session_state.page == "events":
    st.title("📝 Gestion des Événements")
    if not st.session_state.apps: 
        st.warning("Ajoutez des apps.")
    else:
        df_evts = pd.DataFrame(st.session_state.events if st.session_state.events else None)
        cols = ["app", "env", "type", "d1", "d2", "h1", "h2", "comment"]
        display_df = df_evts[cols] if not df_evts.empty else pd.DataFrame(columns=cols)
        edited_evts = st.data_editor(display_df, num_rows="dynamic", use_container_width=True, hide_index=True, 
                                     column_config={"app": st.column_config.SelectboxColumn("App", options=st.session_state.apps),
                                                    "env": st.column_config.SelectboxColumn("Env", options=["PROD", "PRÉPROD", "RECETTE"]),
                                                    "type": st.column_config.SelectboxColumn("Type", options=["MEP", "INCIDENT", "MAINTENANCE", "TEST", "TNR", "MORATOIRE"])}, key="ed_evts")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            save_btn = st.button("💾 Sauvegarder", type="primary", use_container_width=True)
        
        if save_btn:
            with st.spinner("Sauvegarde en cours..."):
                cleaned = []
                for _, r in edited_evts.iterrows():
                    if pd.notnull(r["app"]) and pd.notnull(r["d1"]):
                        d2 = r["d2"] if pd.notnull(r["d2"]) else r["d1"]
                        cleaned.append({"app": r["app"], "env": r["env"], "type": r["type"], "d1": r["d1"], "d2": d2, "h1": r.get("h1","00:00"), "h2": r.get("h2","23:59"), "comment": str(r.get("comment",""))})
                save_events_db(cleaned)
                st.success("✅ Événements sauvegardés avec succès !")
                time.sleep(1)
                del st.session_state.data_loaded
                st.rerun()

elif st.session_state.page == "planning":
    st.title(f"📅 Planning Visuel {sel_year}")
    env_sel = st.radio("Secteur :", ["PROD", "PRÉPROD", "RECETTE"], horizontal=True)
    fr_holidays = holidays.France(years=sel_year)
    tabs = st.tabs(MONTHS_FR)

    for i, tab in enumerate(tabs):
        with tab:
            m = i + 1
            days_in_m = calendar.monthrange(sel_year, m)[1]
            dates_m = [date(sel_year, m, d) for d in range(1, days_in_m + 1)]
            
            # FIX 1 : Afficher toutes les apps même sans événements
            if not st.session_state.apps:
                st.info("Aucune application enregistrée.")
                continue

            # CONSTRUCTION TABLEAU
            html = f'<div class="planning-wrap"><table class="planning-table"><thead><tr><th class="app-header">Application</th>'
            
            # En-têtes des jours
            for d in dates_m:
                th_c = "today-header" if d == TODAY else ""
                day_l = ["L","M","M","J","V","S","D"][d.weekday()]
                html += f'<th class="{th_c}">{d.day}<br>{day_l}</th>'
            html += '</tr></thead><tbody>'

            # FIX 1 : Parcourir TOUTES les apps (pas seulement celles avec événements)
            for app_n in st.session_state.apps:
                html += f'<tr><td class="app-name">{app_n}</td>'
                
                # FIX 3 : Pour chaque jour, vérifier si un événement couvre ce jour
                for d in dates_m:
                    td_class = []
                    content = ""
                    tooltip_html = ""
                    
                    # Styles de base
                    if d == TODAY: 
                        td_class.append("today-col")
                    if d.weekday() >= 5: 
                        td_class.append("weekend")
                    
                    # Vérifier jour férié
                    h_name = fr_holidays.get(d)
                    if h_name:
                        td_class.append("ferie")
                        if d.weekday() < 5:  # Afficher emoji seulement si pas week-end
                            content = "🎉"
                    
                    # FIX 3 : Chercher un événement qui COUVRE ce jour (pas seulement qui commence ce jour)
                    matching_event = None
                    for ev in st.session_state.events:
                        if ev["app"] == app_n and ev["env"] == env_sel:
                            # Vérifier si le jour actuel est dans la plage de l'événement
                            if ev["d1"] <= d <= ev["d2"]:
                                matching_event = ev
                                break
                    
                    # Si événement trouvé pour ce jour
                    if matching_event:
                        ev = matching_event
                        t_raw = str(ev["type"]).upper()
                        
                        # Déterminer la classe CSS
                        if "MEP" in t_raw:
                            t_cls = "mep"
                        elif "INC" in t_raw:
                            t_cls = "inc"
                        elif "MAI" in t_raw:
                            t_cls = "mai"
                        elif "TEST" in t_raw:
                            t_cls = "test"
                        elif "TNR" in t_raw:
                            t_cls = "tnr"
                        elif "MOR" in t_raw:
                            t_cls = "mor"
                        else:
                            t_cls = "mep"  # Par défaut
                        
                        content = f'<div class="event-cell {t_cls}">{t_raw[:3]}</div>'
                        
                        # Construction du tooltip
                        dur = (ev["d2"] - ev["d1"]).days + 1
                        comment_text = str(ev.get('comment', '-')).replace('<', '&lt;').replace('>', '&gt;')
                        
                        tooltip_content = f'''<div class="tooltip-box">
<strong style="color:#60a5fa; font-size:13px; display:block; margin-bottom:8px;">📋 {ev['type']}</strong>
<span class="tooltip-label">📱 App:</span> {ev['app']}<br>
<span class="tooltip-label">⏰ Heures:</span> {ev.get('h1','00:00')} - {ev.get('h2','23:59')}<br>
<span class="tooltip-label">📅 Dates:</span> {ev['d1'].strftime('%d/%m')} au {ev['d2'].strftime('%d/%m')}<br>
<span class="tooltip-label">⏱️ Durée:</span> {dur} jour(s)<br>
{f'<span class="tooltip-label">🎉 Férié:</span> {h_name}<br>' if h_name else ''}<span class="tooltip-label">💬 Note:</span> {comment_text if comment_text != '-' else '<i>Aucune</i>'}
</div>'''
                        
                        # Assemblage de la cellule avec tooltip
                        class_str = " ".join(td_class) if td_class else ""
                        html += f'<td class="{class_str} has-tooltip">{content}{tooltip_content}</td>'
                    else:
                        # Cellule sans événement
                        class_str = " ".join(td_class) if td_class else ""
                        html += f'<td class="{class_str}">{content}</td>'
                
                html += '</tr>'
            
            html += '</tbody></table></div>'
            st.markdown(html, unsafe_allow_html=True)


