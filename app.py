import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# Utilisation de la mémoire vive (Session State) pour éviter la boucle
if 'apps' not in st.session_state:
    st.session_state.apps = ["PRAC"] # On en met une par défaut pour tester
if 'events' not in st.session_state:
    st.session_state.events = []

st.title("🚀 Mon Planning IT - Mode Stable")

# --- 2. BARRE LATÉRALE ---
with st.sidebar:
    st.header("⚙️ Configuration")
    if st.button("🔄 Forcer l'actualisation"):
        st.rerun()
    
    st.divider()
    
    with st.expander("📝 Gérer les Applis"):
        new_a = st.text_input("Nom de l'appli").upper()
        if st.button("Ajouter"):
            if new_a and new_a not in st.session_state.apps:
                st.session_state.apps.append(new_a)
                st.success("Ajoutée !")
    
    st.divider()
    
    st.subheader("➕ Nouvel événement")
    with st.form("form_add", clear_on_submit=True):
        f_app = st.selectbox("Application", st.session_state.apps)
        f_env = st.selectbox("Env", ["PROD", "PRÉPROD", "RECETTE"])
        f_type = st.selectbox("Type", ["MEP", "Incident", "Maintenance", "Test", "Moratoire"])
        f_d1 = st.date_input("Du")
        f_d2 = st.date_input("Au")
        if st.form_submit_button("Enregistrer"):
            st.session_state.events.append({
                'app': f_app, 'env': f_env, 'type': f_type, 'd1': f_d1, 'd2': f_d2
            })
            st.success("Enregistré !")

# --- 3. AFFICHAGE ---
tab1, tab2, tab3 = st.tabs(["PROD", "PRÉPROD", "RECETTE"])

def show_env(env_name):
    if not st.session_state.apps:
        st.info("Ajoutez une application dans la barre latérale.")
        return

    # Création d'un tableau de dates
    start_date = date(2026, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(31)] # On teste sur 31 jours
    
    # Préparation des données pour le tableau
    data = {"Application": sorted(st.session_state.apps)}
    
    for d in dates:
        col_name = d.strftime("%d/%m")
        data[col_name] = []
        for app in data["Application"]:
            # On cherche si un événement existe pour ce jour/app/env
            status = ""
            if d.weekday() >= 5: status = "WE"
            
            for ev in st.session_state.events:
                if ev['app'] == app and ev['env'] == env_name:
                    if ev['d1'] <= d <= ev['d2']:
                        status = ev['type']
            
            data[col_name].append(status)

    df = pd.DataFrame(data)
    
    # Affichage du tableau avec des couleurs
    def color_cells(val):
        color = 'white'
        if val == "MEP": color = "#0070C0; color: white"
        elif val == "Incident": color = "#FF0000; color: white"
        elif val == "Maintenance": color = "#FFC000"
        elif val == "Test": color = "#00B050; color: white"
        elif val == "WE": color = "#D9D9D9"
        return f'background-color: {color}'

    st.dataframe(df.style.applymap(color_cells), height=400, use_container_width=True)

with tab1: show_env("PROD")
with tab2: show_env("PRÉPROD")
with tab3: show_env("RECETTE")


