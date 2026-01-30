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
# ==================================================
# Indicateur d'environnement
# On utilise .get() pour éviter que l'app plante si la clé n'existe pas encore
env_type = st.secrets["supabase"].get("env", "PRODUCTION")

if env_type == "DEVELOPPEMENT":
    st.sidebar.warning("⚠️ MODE DÉVELOPPEMENT")
    st.sidebar.caption("Base : Planning-IT-DEV")
@st.cache_resource
# ==================================================
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
    if not supabase: return [], [], [], [], []
    try:
        # Charger les applications
        res_apps = supabase.table("applications").select("*").order("ordre", desc=False).execute()
        apps_full = res_apps.data
        apps_names = [row['nom'] for row in apps_full]
        
        # Charger les projets
        res_projets = supabase.table("projets").select("*").order("projet", desc=False).execute()
        projets_full = res_projets.data
        projets_names = [row['projet'] for row in projets_full]
        
        # Charger les événements
        res_evts = supabase.table("evenements").select("*").execute()
        evts_data = res_evts.data
        for ev in evts_data:
            ev['d1'] = pd.to_datetime(ev['d1']).date()
            ev['d2'] = pd.to_datetime(ev['d2']).date()
            if 'h1' not in ev: ev['h1'] = "00:00"
            if 'h2' not in ev: ev['h2'] = "23:59"
            if 'projet' not in ev: ev['projet'] = None
        return apps_names, apps_full, evts_data, projets_names, projets_full
    except Exception as e:
        st.error(f"Erreur lecture : {e}")
        return [], [], [], [], []

def save_apps_db(df_apps):
    if not supabase: return
    try:
        supabase.table("applications").delete().neq("id", 0).execute()
        data = [{"nom": str(row['Nom']).upper().strip(), "ordre": int(row['Ordre'])} for _, row in df_apps.iterrows() if row['Nom']]
        if data: supabase.table("applications").insert(data).execute()
    except Exception as e: st.error(f"Erreur Apps : {e}")

def save_projets_db(projet_list):
    if not supabase: return
    try:
        supabase.table("projets").delete().neq("id", 0).execute()
        if projet_list:
            data = [{"projet": str(p).upper().strip()} for p in projet_list if p and str(p).strip()]
            if data: supabase.table("projets").insert(data).execute()
    except Exception as e: st.error(f"Erreur Projets : {e}")

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
                "comment": str(ev['comment']),
                "projet": ev.get('projet') if ev.get('projet') else None
            } for ev in event_list]
            supabase.table("evenements").insert(data).execute()
    except Exception as e: st.error(f"Erreur Events : {e}")

# --- VARIABLES ---
TODAY = date.today()
MONTHS_FR = ["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]

if "data_loaded" not in st.session_state:
    an, af, ed, pn, pf = load_data()
    st.session_state.apps, st.session_state.apps_data, st.session_state.events = an, af, ed
    st.session_state.projets, st.session_state.projets_data = pn, pf
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
    
    /* Événements multiples - bandes horizontales */
    .multi-event {
        display: flex;
        flex-direction: column;
        width: 100%;
        height: 100%;
        cursor: pointer;
    }
    .multi-event .event-band {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 9px;
        line-height: 1;
    }
    
    .mep, .bg-mep { background-color: #0070C0; } 
    .inc, .bg-inc { background-color: #FF0000; } 
    .mai, .bg-mai { background-color: #FFC000; color: black; } 
    .test, .bg-test { background-color: #00B050; } 
    .tnr, .bg-tnr { background-color: #70AD47; }
    .mor, .bg-mor { background-color: #9600C8; }
    
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
    
    /* Tooltip avec position fixed pour sortir du conteneur */
    .has-tooltip { position: relative; }
    .has-tooltip .tooltip-box {
        visibility: hidden;
        opacity: 0;
        width: 320px;
        max-height: 400px;
        overflow-y: auto;
        background-color: #1e293b;
        color: #fff;
        border-radius: 6px;
        padding: 14px;
        position: fixed;
        z-index: 99999;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        font-size: 12px;
        text-align: left;
        line-height: 1.7;
        pointer-events: none;
        transition: opacity 0.15s, visibility 0.15s;
    }
    
    /* Scrollbar du tooltip */
    .has-tooltip .tooltip-box::-webkit-scrollbar {
        width: 6px;
    }
    .has-tooltip .tooltip-box::-webkit-scrollbar-track {
        background: #334155;
        border-radius: 3px;
    }
    .has-tooltip .tooltip-box::-webkit-scrollbar-thumb {
        background: #64748b;
        border-radius: 3px;
    }
    
    .has-tooltip:hover .tooltip-box {
        visibility: visible;
        opacity: 1;
        pointer-events: auto;
    }
    
    /* Séparateur entre événements dans le tooltip */
    .tooltip-separator {
        border-top: 1px solid #475569;
        margin: 10px 0;
        padding-top: 10px;
    }
    
    /* Badge compteur d'événements */
    .event-count {
        position: absolute;
        top: 2px;
        right: 2px;
        background-color: rgba(0,0,0,0.5);
        color: white;
        font-size: 8px;
        font-weight: bold;
        padding: 1px 4px;
        border-radius: 3px;
    }
</style>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // Fonction pour positionner les tooltips
    function setupTooltips() {
        const cells = document.querySelectorAll('.has-tooltip');
        
        cells.forEach(cell => {
            const tooltip = cell.querySelector('.tooltip-box');
            if (!tooltip) return;
            
            cell.addEventListener('mouseenter', function(e) {
                const rect = cell.getBoundingClientRect();
                const tooltipRect = tooltip.getBoundingClientRect();
                const viewportHeight = window.innerHeight;
                const viewportWidth = window.innerWidth;
                
                // Position horizontale - centré sur la cellule
                let left = rect.left + rect.width / 2 - 160; // 160 = moitié de 320px
                
                // Ajuster si dépasse à droite
                if (left + 320 > viewportWidth - 10) {
                    left = viewportWidth - 330;
                }
                // Ajuster si dépasse à gauche
                if (left < 10) {
                    left = 10;
                }
                
                // Position verticale - au-dessus par défaut
                let top = rect.top - tooltip.offsetHeight - 10;
                
                // Si pas assez de place en haut, mettre en bas
                if (top < 10) {
                    top = rect.bottom + 10;
                }
                
                // Si toujours pas assez de place (en bas), centrer verticalement
                if (top + tooltip.offsetHeight > viewportHeight - 10) {
                    top = Math.max(10, (viewportHeight - tooltip.offsetHeight) / 2);
                }
                
                tooltip.style.left = left + 'px';
                tooltip.style.top = top + 'px';
            });
        });
    }
    
    // Setup initial et après chaque changement Streamlit
    setupTooltips();
    
    // Observer les changements du DOM pour les tabs Streamlit
    const observer = new MutationObserver(function(mutations) {
        setupTooltips();
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
});
</script>
""", unsafe_allow_html=True)

# ==================================================
# 3. SIDEBAR
# ==================================================
with st.sidebar:
    st.title("📌 Menu")
    if st.button("📅 Planning", use_container_width=True): st.session_state.page = "planning"; st.rerun()
    if st.button("📝 Événements", use_container_width=True): st.session_state.page = "events"; st.rerun()
    if st.button("📱 Applications", use_container_width=True): st.session_state.page = "apps"; st.rerun()
    if st.button("📁 Projets", use_container_width=True): st.session_state.page = "projets"; st.rerun()
    st.divider()
    years_list = [2025, 2026, 2027, 2028]
    sel_year = st.selectbox("Année", years_list, index=years_list.index(TODAY.year) if TODAY.year in years_list else 1)
    st.divider()
    
    # FORMULAIRE D'AJOUT RAPIDE (uniquement sur la page planning)
    if st.session_state.page == "planning" and st.session_state.apps:
        st.markdown("### ➕ Ajout rapide")
        
        with st.form("quick_add_form", clear_on_submit=True):
            q_app = st.selectbox("📱 Application", st.session_state.apps)
            q_env = st.selectbox("🌐 Environnement", ["PROD", "PRÉPROD", "RECETTE"])
            q_type = st.selectbox("🏷️ Type", ["MEP", "INCIDENT", "MAINTENANCE", "TEST", "TNR", "MORATOIRE"])
            
            # Projet (optionnel)
            projet_options = ["(Aucun)"] + st.session_state.projets
            q_projet = st.selectbox("📁 Projet", projet_options)
            
            col1, col2 = st.columns(2)
            with col1:
                q_d1 = st.date_input("📅 Début", value=TODAY)
            with col2:
                q_d2 = st.date_input("📅 Fin", value=TODAY)
            
            col3, col4 = st.columns(2)
            with col3:
                q_h1 = st.text_input("⏰ H. début", value="00:00", max_chars=5)
            with col4:
                q_h2 = st.text_input("⏰ H. fin", value="23:59", max_chars=5)
            
            q_comment = st.text_area("💬 Commentaire", placeholder="Détails...", height=80)
            
            submitted = st.form_submit_button("✅ Ajouter", use_container_width=True, type="primary")
            
            if submitted:
                new_event = {
                    "app": q_app,
                    "env": q_env,
                    "type": q_type,
                    "d1": q_d1,
                    "d2": q_d2,
                    "h1": q_h1,
                    "h2": q_h2,
                    "comment": q_comment,
                    "projet": q_projet if q_projet != "(Aucun)" else None
                }
                with st.spinner("Ajout en cours..."):
                    st.session_state.events.append(new_event)
                    save_events_db(st.session_state.events)
                    st.success("✅ Événement ajouté !")
                    time.sleep(0.5)
                    del st.session_state.data_loaded
                    st.rerun()
        
        st.divider()
    
    if st.button("🔄 Actualiser"): del st.session_state.data_loaded; st.rerun()

# ==================================================
# 4. PAGES
# ==================================================

if st.session_state.page == "apps":
    st.title("📱 Gestion des Applications")
    
    # Préparation des données
    clean_data = [{"Nom": i.get('nom', ''), "Ordre": i.get('ordre', 0)} for i in st.session_state.apps_data]
    df_apps = pd.DataFrame(clean_data if clean_data else None, columns=["Nom", "Ordre"])
    
    # Data editor avec configuration
    edited_apps = st.data_editor(
        df_apps, 
        num_rows="dynamic", 
        use_container_width=True, 
        hide_index=True, 
        key="ed_apps",
        column_config={
            "Nom": st.column_config.TextColumn("Nom", help="Nom de l'application (majuscules)", max_chars=50, required=True),
            "Ordre": st.column_config.NumberColumn("Ordre", help="Ordre d'affichage", min_value=0, max_value=999, step=1, required=True)
        }
    )
    
    # Afficher le nombre d'applications
    nb_apps = len([row for _, row in edited_apps.iterrows() if row['Nom'] and str(row['Nom']).strip()])
    st.caption(f"📊 {nb_apps} application(s)")
    
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        save_btn = st.button("💾 Sauvegarder", type="primary", use_container_width=True)
    with col2:
        cancel_btn = st.button("↩️ Annuler", use_container_width=True)
    
    if save_btn:
        # Validation
        valid_apps = []
        errors = []
        
        for idx, row in edited_apps.iterrows():
            nom = str(row['Nom']).strip() if pd.notnull(row['Nom']) else ""
            
            if nom:  # Seulement si le nom n'est pas vide
                if pd.isnull(row['Ordre']):
                    errors.append(f"⚠️ Ligne {idx+1}: L'ordre est obligatoire pour '{nom}'")
                else:
                    valid_apps.append({"Nom": nom.upper(), "Ordre": int(row['Ordre'])})
        
        if errors:
            for err in errors:
                st.error(err)
        elif not valid_apps:
            st.warning("⚠️ Aucune application à sauvegarder")
        else:
            # Vérifier les doublons
            noms = [app['Nom'] for app in valid_apps]
            if len(noms) != len(set(noms)):
                st.error("⚠️ Il y a des noms d'applications en double")
            else:
                with st.spinner("Sauvegarde en cours..."):
                    df_to_save = pd.DataFrame(valid_apps).sort_values(by="Ordre")
                    save_apps_db(df_to_save)
                    st.success(f"✅ {len(valid_apps)} application(s) sauvegardée(s) avec succès !")
                    time.sleep(1)
                    del st.session_state.data_loaded
                    st.rerun()
    
    if cancel_btn:
        del st.session_state.data_loaded
        st.rerun()

elif st.session_state.page == "projets":
    st.title("📁 Gestion des Projets")
    
    # Préparation des données
    df_projets = pd.DataFrame({"Projet": st.session_state.projets}) if st.session_state.projets else pd.DataFrame(columns=["Projet"])
    
    # Data editor
    edited_projets = st.data_editor(
        df_projets, 
        num_rows="dynamic", 
        use_container_width=True, 
        hide_index=True, 
        key="ed_projets",
        column_config={
            "Projet": st.column_config.TextColumn("Nom du projet", help="Nom du projet (majuscules)", max_chars=100, required=True)
        }
    )
    
    # Afficher le nombre de projets
    nb_projets = len([row for _, row in edited_projets.iterrows() if row['Projet'] and str(row['Projet']).strip()])
    st.caption(f"📊 {nb_projets} projet(s)")
    
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        save_btn = st.button("💾 Sauvegarder", type="primary", use_container_width=True, key="save_projets")
    with col2:
        cancel_btn = st.button("↩️ Annuler", use_container_width=True, key="cancel_projets")
    
    if save_btn:
        # Récupérer les projets valides
        valid_projets = [str(row['Projet']).upper().strip() for _, row in edited_projets.iterrows() if row['Projet'] and str(row['Projet']).strip()]
        
        # Vérifier les doublons
        if len(valid_projets) != len(set(valid_projets)):
            st.error("⚠️ Il y a des noms de projets en double")
        else:
            with st.spinner("Sauvegarde en cours..."):
                save_projets_db(valid_projets)
                st.success(f"✅ {len(valid_projets)} projet(s) sauvegardé(s) avec succès !")
                time.sleep(1)
                del st.session_state.data_loaded
                st.rerun()
    
    if cancel_btn:
        del st.session_state.data_loaded
        st.rerun()

elif st.session_state.page == "events":
    st.title("📝 Gestion des Événements")
    if not st.session_state.apps: 
        st.warning("⚠️ Ajoutez d'abord des applications dans l'onglet 📱 Applications")
    else:
        # FILTRES RAPIDES
        st.markdown("### 🔍 Filtres rapides")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            filter_app = st.selectbox("📱 Application", ["Toutes"] + st.session_state.apps, key="filter_app")
        with col_f2:
            filter_env = st.selectbox("🌐 Environnement", ["Tous", "PROD", "PRÉPROD", "RECETTE"], key="filter_env")
        with col_f3:
            filter_type = st.selectbox("🏷️ Type", ["Tous", "MEP", "INCIDENT", "MAINTENANCE", "TEST", "TNR", "MORATOIRE"], key="filter_type")
        with col_f4:
            filter_projet = st.selectbox("📁 Projet", ["Tous", "(Sans projet)"] + st.session_state.projets, key="filter_projet")
        
        st.divider()
        
        # Préparation des données
        df_evts = pd.DataFrame(st.session_state.events if st.session_state.events else None)
        cols = ["app", "env", "type", "projet", "d1", "d2", "h1", "h2", "comment"]
        
        if not df_evts.empty:
            # S'assurer que la colonne projet existe
            if 'projet' not in df_evts.columns:
                df_evts['projet'] = None
            display_df = df_evts[cols].copy()
        else:
            display_df = pd.DataFrame(columns=cols)
        
        # Appliquer les filtres pour l'affichage
        filtered_df = display_df.copy()
        if filter_app != "Toutes":
            filtered_df = filtered_df[filtered_df['app'] == filter_app]
        if filter_env != "Tous":
            filtered_df = filtered_df[filtered_df['env'] == filter_env]
        if filter_type != "Tous":
            filtered_df = filtered_df[filtered_df['type'] == filter_type]
        if filter_projet == "(Sans projet)":
            filtered_df = filtered_df[filtered_df['projet'].isna() | (filtered_df['projet'] == "") | (filtered_df['projet'].isnull())]
        elif filter_projet != "Tous":
            filtered_df = filtered_df[filtered_df['projet'] == filter_projet]
        
        # Options pour le selectbox projet (avec option vide)
        projet_options_edit = [""] + st.session_state.projets
        
        # Data editor avec configuration améliorée
        edited_evts = st.data_editor(
            filtered_df, 
            num_rows="dynamic", 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "app": st.column_config.SelectboxColumn("App", options=st.session_state.apps, help="Application concernée", required=True),
                "env": st.column_config.SelectboxColumn("Env", options=["PROD", "PRÉPROD", "RECETTE"], help="Environnement", required=True),
                "type": st.column_config.SelectboxColumn("Type", options=["MEP", "INCIDENT", "MAINTENANCE", "TEST", "TNR", "MORATOIRE"], help="Type d'événement", required=True),
                "projet": st.column_config.SelectboxColumn("Projet", options=projet_options_edit, help="Projet associé (optionnel)", required=False),
                "d1": st.column_config.DateColumn("Date début", format="DD/MM/YYYY", help="Date de début", required=True),
                "d2": st.column_config.DateColumn("Date fin", format="DD/MM/YYYY", help="Date de fin", required=True),
                "h1": st.column_config.TextColumn("H. début", help="Heure début (HH:MM)", default="00:00", max_chars=5),
                "h2": st.column_config.TextColumn("H. fin", help="Heure fin (HH:MM)", default="23:59", max_chars=5),
                "comment": st.column_config.TextColumn("Commentaire", help="Détails de l'événement", max_chars=1000)
            },
            key="ed_evts"
        )
        
        # Afficher le nombre d'événements
        nb_events = len([r for _, r in edited_evts.iterrows() if pd.notnull(r.get("app")) and pd.notnull(r.get("d1"))])
        nb_total = len([r for _, r in display_df.iterrows() if pd.notnull(r.get("app")) and pd.notnull(r.get("d1"))])
        
        if filter_app != "Toutes" or filter_env != "Tous" or filter_type != "Tous" or filter_projet != "Tous":
            st.caption(f"📊 {nb_events} événement(s) affiché(s) sur {nb_total} au total (filtres actifs)")
        else:
            st.caption(f"📊 {nb_events} événement(s)")
        
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            save_btn = st.button("💾 Sauvegarder", type="primary", use_container_width=True)
        with col2:
            cancel_btn = st.button("↩️ Annuler", use_container_width=True)
        
        if save_btn:
            # IMPORTANT: Si des filtres sont actifs, on doit fusionner avec les événements non filtrés
            if filter_app != "Toutes" or filter_env != "Tous" or filter_type != "Tous" or filter_projet != "Tous":
                st.warning("⚠️ Des filtres sont actifs. La sauvegarde ne modifiera que les événements affichés. Les autres événements seront conservés.")
            
            # Validation
            cleaned = []
            errors = []
            
            for idx, r in edited_evts.iterrows():
                # Vérifier que les champs obligatoires sont remplis
                if pd.notnull(r.get("app")):
                    ligne = idx + 1
                    
                    # Validation des champs obligatoires
                    if pd.isnull(r.get("env")):
                        errors.append(f"⚠️ Ligne {ligne}: Environnement obligatoire")
                        continue
                    if pd.isnull(r.get("type")):
                        errors.append(f"⚠️ Ligne {ligne}: Type obligatoire")
                        continue
                    if pd.isnull(r.get("d1")):
                        errors.append(f"⚠️ Ligne {ligne}: Date début obligatoire")
                        continue
                    
                    # Date de fin par défaut = date de début
                    d1 = r["d1"]
                    d2 = r["d2"] if pd.notnull(r.get("d2")) else d1
                    
                    # Validation cohérence des dates
                    if d2 < d1:
                        errors.append(f"⚠️ Ligne {ligne}: Date fin avant date début")
                        continue
                    
                    # Validation heures
                    h1 = str(r.get("h1", "00:00")).strip() if pd.notnull(r.get("h1")) else "00:00"
                    h2 = str(r.get("h2", "23:59")).strip() if pd.notnull(r.get("h2")) else "23:59"
                    
                    # Vérification format HH:MM basique
                    if not (len(h1) == 5 and h1[2] == ":"):
                        errors.append(f"⚠️ Ligne {ligne}: Format heure début invalide (attendu HH:MM)")
                        continue
                    if not (len(h2) == 5 and h2[2] == ":"):
                        errors.append(f"⚠️ Ligne {ligne}: Format heure fin invalide (attendu HH:MM)")
                        continue
                    
                    # Commentaire et projet
                    comment = str(r.get("comment", "")).strip()
                    projet = r.get("projet") if pd.notnull(r.get("projet")) and r.get("projet") != "" else None
                    
                    cleaned.append({
                        "app": r["app"],
                        "env": r["env"],
                        "type": r["type"],
                        "d1": d1,
                        "d2": d2,
                        "h1": h1,
                        "h2": h2,
                        "comment": comment,
                        "projet": projet
                    })
            
            # Afficher les erreurs ou sauvegarder
            if errors:
                for err in errors:
                    st.error(err)
            else:
                with st.spinner("Sauvegarde en cours..."):
                    # Si des filtres sont actifs, fusionner avec les événements non affichés
                    if filter_app != "Toutes" or filter_env != "Tous" or filter_type != "Tous" or filter_projet != "Tous":
                        # Garder les événements qui ne correspondent pas aux filtres
                        final_events = []
                        for ev in st.session_state.events:
                            keep = False
                            if filter_app != "Toutes" and ev.get('app') != filter_app:
                                keep = True
                            elif filter_env != "Tous" and ev.get('env') != filter_env:
                                keep = True
                            elif filter_type != "Tous" and ev.get('type') != filter_type:
                                keep = True
                            elif filter_projet == "(Sans projet)" and ev.get('projet') and ev.get('projet') != "":
                                keep = True
                            elif filter_projet != "Tous" and filter_projet != "(Sans projet)" and ev.get('projet') != filter_projet:
                                keep = True
                            
                            if keep:
                                final_events.append(ev)
                        
                        # Ajouter les événements édités
                        final_events.extend(cleaned)
                        save_events_db(final_events)
                        st.success(f"✅ Sauvegarde réussie ! ({len(cleaned)} événement(s) modifié(s), {len(final_events)} au total)")
                    else:
                        save_events_db(cleaned)
                        st.success(f"✅ {len(cleaned)} événement(s) sauvegardé(s) avec succès !")
                    
                    time.sleep(1)
                    del st.session_state.data_loaded
                    st.rerun()
        
        if cancel_btn:
            del st.session_state.data_loaded
            st.rerun()

elif st.session_state.page == "planning":
    st.title(f"📅 Planning Visuel {sel_year}")
    
    # Sélection de l'environnement
    env_sel = st.radio("Secteur :", ["PROD", "PRÉPROD", "RECETTE"], horizontal=True)
    
    # Filtre par projet (uniquement pour RECETTE)
    projet_filter = None
    if env_sel == "RECETTE" and st.session_state.projets:
        projet_options = ["📋 Afficher tout", "📋 Afficher tout (hors projet)"] + st.session_state.projets
        projet_filter = st.selectbox("📁 Filtrer par projet :", projet_options, key="planning_projet_filter")
        
        if projet_filter == "📋 Afficher tout":
            st.caption("ℹ️ Affichage de tous les événements")
        elif projet_filter == "📋 Afficher tout (hors projet)":
            st.caption("ℹ️ Affichage uniquement des événements sans projet associé")
        else:
            st.caption(f"ℹ️ Affichage du projet **{projet_filter}** + événements sans projet")
    
    fr_holidays = holidays.France(years=sel_year)
    tabs = st.tabs(MONTHS_FR)

    # Fonction helper pour obtenir la classe CSS d'un type d'événement
    def get_event_class(event_type):
        t_raw = str(event_type).upper()
        if "MEP" in t_raw:
            return "mep"
        elif "INC" in t_raw:
            return "inc"
        elif "MAI" in t_raw:
            return "mai"
        elif "TEST" in t_raw:
            return "test"
        elif "TNR" in t_raw:
            return "tnr"
        elif "MOR" in t_raw:
            return "mor"
        return "mep"
    
    # Fonction pour filtrer les événements selon le projet (RECETTE uniquement)
    def should_show_event(ev, env_sel, projet_filter):
        # Vérifier l'environnement
        if ev["env"] != env_sel:
            return False
        
        # Si pas en RECETTE ou pas de filtre projet, afficher tout
        if env_sel != "RECETTE" or projet_filter is None:
            return True
        
        ev_projet = ev.get("projet")
        has_no_projet = ev_projet is None or ev_projet == "" or pd.isna(ev_projet)
        
        if projet_filter == "📋 Afficher tout":
            # Afficher TOUS les événements (avec ou sans projet)
            return True
        elif projet_filter == "📋 Afficher tout (hors projet)":
            # Afficher uniquement les événements SANS projet
            return has_no_projet
        else:
            # Afficher le projet sélectionné + les événements sans projet
            return has_no_projet or ev_projet == projet_filter

    for i, tab in enumerate(tabs):
        with tab:
            m = i + 1
            days_in_m = calendar.monthrange(sel_year, m)[1]
            dates_m = [date(sel_year, m, d) for d in range(1, days_in_m + 1)]
            
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

            for app_n in st.session_state.apps:
                html += f'<tr><td class="app-name">{app_n}</td>'
                
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
                        if d.weekday() < 5:
                            content = "🎉"
                    
                    # Collecter les événements qui couvrent ce jour (avec filtre projet si RECETTE)
                    matching_events = []
                    for ev in st.session_state.events:
                        if ev["app"] == app_n and should_show_event(ev, env_sel, projet_filter):
                            if ev["d1"] <= d <= ev["d2"]:
                                matching_events.append(ev)
                    
                    # Si des événements sont trouvés pour ce jour
                    if matching_events:
                        if len(matching_events) == 1:
                            # UN SEUL événement - affichage classique
                            ev = matching_events[0]
                            t_cls = get_event_class(ev["type"])
                            t_raw = str(ev["type"]).upper()
                            content = f'<div class="event-cell {t_cls}">{t_raw[:3]}</div>'
                        else:
                            # PLUSIEURS événements - affichage en bandes
                            content = '<div class="multi-event">'
                            for ev in matching_events:
                                t_cls = get_event_class(ev["type"])
                                t_raw = str(ev["type"]).upper()
                                content += f'<div class="event-band bg-{t_cls}">{t_raw[:3]}</div>'
                            content += '</div>'
                        
                        # Construction du tooltip avec TOUS les événements
                        tooltip_parts = []
                        for idx, ev in enumerate(matching_events):
                            dur = (ev["d2"] - ev["d1"]).days + 1
                            comment_text = str(ev.get('comment', '-')).replace('<', '&lt;').replace('>', '&gt;')
                            projet_text = ev.get('projet') if ev.get('projet') and ev.get('projet') != "" else None
                            
                            separator = '<div class="tooltip-separator"></div>' if idx > 0 else ''
                            
                            projet_line = f'<span class="tooltip-label">📁 Projet:</span> {projet_text}<br>' if projet_text else ''
                            
                            tooltip_parts.append(f'''{separator}
<strong style="color:#60a5fa; font-size:13px; display:block; margin-bottom:8px;">📋 {ev['type']}</strong>
<span class="tooltip-label">📱 App:</span> {ev['app']}<br>
{projet_line}<span class="tooltip-label">⏰ Heures:</span> {ev.get('h1','00:00')} - {ev.get('h2','23:59')}<br>
<span class="tooltip-label">📅 Dates:</span> {ev['d1'].strftime('%d/%m')} au {ev['d2'].strftime('%d/%m')}<br>
<span class="tooltip-label">⏱️ Durée:</span> {dur} jour(s)<br>
<span class="tooltip-label">💬 Note:</span> {comment_text if comment_text and comment_text != '-' else '<i>Aucune</i>'}''')
                        
                        # Ajouter info férié si applicable
                        if h_name:
                            tooltip_parts.append(f'<br><span class="tooltip-label">🎉 Férié:</span> {h_name}')
                        
                        tooltip_content = f'''<div class="tooltip-box">{''.join(tooltip_parts)}</div>'''
                        
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
