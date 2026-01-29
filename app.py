import streamlit as st
import pandas as pd
import calendar
from datetime import date

# ==================================================
# 1. CONFIGURATION & STATE
# ==================================================
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# Jours fériés 2026
JOURS_FERIES_2026 = [
    date(2026, 1, 1), date(2026, 4, 6), date(2026, 5, 1), date(2026, 5, 8),
    date(2026, 5, 14), date(2026, 5, 25), date(2026, 7, 14), date(2026, 8, 15),
    date(2026, 11, 1), date(2026, 11, 11), date(2026, 12, 25),
]

# Initialisation des variables
if "apps" not in st.session_state: st.session_state.apps = []
if "events" not in st.session_state: st.session_state.events = []
if "page" not in st.session_state: st.session_state.page = "planning"
if "admin_unlocked" not in st.session_state: st.session_state.admin_unlocked = False

# ==================================================
# 2. CSS (DESIGN PRO & TOOLTIP FIXED)
# ==================================================
st.markdown("""
<style>
    /* WRAPPER : On ajoute beaucoup d'espace en bas pour le tooltip */
    .planning-wrap { 
        overflow-x: auto; 
        padding-bottom: 120px; /* Espace réservé pour l'infobulle */
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
    
    /* HEADER */
    .planning-table th { background-color: #f8fafc; color: #334155; padding: 10px 5px; text-align: center; border-right: 1px solid #e2e8f0; border-bottom: 2px solid #cbd5e1; font-weight: 600; font-size: 11px; }
    .planning-table th.app-header { text-align: left; padding-left: 15px; width: 150px; position: sticky; left: 0; z-index: 20; background-color: #f8fafc; border-right: 2px solid #cbd5e1; }
    
    /* CELLULES */
    .planning-table td { background-color: #ffffff; text-align: center; padding: 0; height: 40px; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; position: relative; }
    .planning-table td.app-name { background-color: #f8fafc; color: #0f172a; font-weight: 600; text-align: left; padding-left: 15px; position: sticky; left: 0; z-index: 10; border-right: 2px solid #cbd5e1; }
    .planning-table td.weekend { background-color: #e2e8f0 !important; }
    .planning-table td.ferie { background-color: #FFE6F0 !important; color: #000; }
    
    /* EVENTS */
    .event-cell { display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; color: white; font-weight: bold; font-size: 10px; }
    .mep { background-color: #0070C0; }
    .inc { background-color: #FF0000; }
    .mai { background-color: #FFC000; color: black; }
    .test { background-color: #00B050; }
    .mor { background-color: #9600C8; }

    /* TOOLTIP FIXÉ */
    .planning-table td:hover { z-index: 100; }
    
    .tooltip-content { 
        visibility: hidden; 
        width: 280px; 
        background-color: #1e293b; 
        color: #fff; 
        text-align: left; 
        border-radius: 6px; 
        padding: 12px; 
        
        /* Positionnement EN DESSOUS pour éviter la coupure en haut */
        position: absolute; 
        top: 100%; /* S'affiche sous la case */
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
    
    /* Flèche vers le haut */
    .tooltip-content::after { 
        content: ""; 
        position: absolute; 
        bottom: 100%; /* Au dessus du tooltip */
        left: 50%; 
        margin-left: -5px; 
        border-width: 5px; 
        border-style: solid; 
        border-color: transparent transparent #1e293b transparent; 
    }
    
    .planning-table td:hover .tooltip-content { visibility: visible; opacity: 1; }
    .tooltip-label { font-weight: bold; color: #4ade80; margin-right: 5px; }
</style>
""", unsafe_allow_html=True)

# ==================================================
# 3. SIDEBAR (NAVIGATION AVEC MÉMOIRE)
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
    
    # Toggle avec clé unique pour la persistance
    mode_admin = st.toggle("Mode Admin", key="toggle_admin")
    
    if mode_admin:
        # Si déjà déverrouillé, on ne redemande pas le mot de passe
        if not st.session_state.admin_unlocked:
            pwd = st.text_input("Mot de passe", type="password")
            if pwd == "admin123":
                st.session_state.admin_unlocked = True
                st.rerun()
            elif pwd:
                st.error("Incorrect")
        
        # Si déverrouillé, on affiche le menu Admin
        if st.session_state.admin_unlocked:
            st.success("🔓 Admin Connecté")
            if st.button("📱 Gérer Applications", use_container_width=True, type="primary"):
                st.session_state.page = "apps"
                st.rerun()
    else:
        # Si on décoche, on verrouille
        st.session_state.admin_unlocked = False
            
    st.divider()
    if st.button("🔄 Rafraîchir l'app"):
        st.rerun()

# ==================================================
# 4. CONTENU DYNAMIQUE
# ==================================================

# --- VUE 1 : GESTION DES APPLICATIONS (ADMIN) ---
if st.session_state.page == "apps":
    if not st.session_state.admin_unlocked:
        st.error("⛔ Accès refusé. Veuillez activer le mode Admin.")
    else:
        st.title("📱 Gestion des Applications")
        st.info("Ajoutez, renommez ou supprimez des applications. L'ordre de la liste définit l'ordre dans le planning.")
        
        df_apps = pd.DataFrame(st.session_state.apps, columns=["Nom Application"])
