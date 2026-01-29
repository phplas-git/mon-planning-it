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
# 3. CSS (DESIGN PRO + TOOLTIP CORRIGÉ)
# ==================================================
css = """
<style>
    /* On retire le conteneur restrictif overflow */
    
    .planning-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        table-layout: fixed; /* Important pour la stabilité */
    }
    
    /* EN-TÊTES */
    .planning-table th {
        background-color: #f1f5f9;
        color: #1e293b;
        padding: 10px 2px;
        text-align: center;
        border-right: 1px solid #e2e8f0;
        border-bottom: 2px solid #cbd5e1;
        font-size: 11px;
    }
    .planning-table th.app-header {
        text-align: left;
        padding-left: 10px;
        width: 150px; /* Largeur fixe pour la colonne appli */
        position: sticky;
        left: 0;
        z-index: 10;
        border-right: 2px solid #cbd5e1;
    }

    /* CELLULES */
    .planning-table td {
        background-color: #ffffff;
        text-align
