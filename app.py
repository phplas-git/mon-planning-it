import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Planning IT Léger", layout="wide")

# Initialisation de la mémoire (RAM)
if 'apps' not in st.session_state:
    st.session_state.apps = ["APPLICATION TEST"]
if 'events' not in st.session_state:
    st.session_state.events = []

# --- 2. BARRE LATÉRALE ---
with st.sidebar:
    st.title("⚙️ Configuration")
    d_start = st.date_input("Début du planning", date(2026, 1, 1))
    
    st.divider()
    
    with st.expander("📝 Ajouter une Appli"):
        new_a = st.text_input("Nom").upper()
        if st.button("Valider"):
            if new_a and new_a not in st.session_state.apps:
                st.session_state.apps.append(new_a)
                st.rerun()
    
    st.divider()
    
    st.subheader("➕ Nouvel événement")
    f_app = st.selectbox("Application", st.session_state.apps)
    f_env = st.selectbox("Environnement", ["PROD", "PRÉPROD", "RECETTE"])
    f_type = st.selectbox("Type", ["MEP", "Incident", "Maintenance", "Test", "Moratoire"])
    f_d1 = st.date_input("Du")
    f_d2 = st.date_input("Au")
    if st.button("Enregistrer l'événement"):
        st.session_state.events.append({
            'app': f_app, 'env': f_env, 'type': f_type, 'd1': f_d1, 'd2': f_d2
        })
        st.success("Enregistré !")

# --- 3. LOGIQUE D'AFFICHAGE (TABLEAU STYLISÉ) ---

def style_planning(env_label):
    if not st.session_state.apps:
        st.write("Aucune application.")
        return

    # On prépare 30 jours de colonnes
    dates = [d_start + timedelta(days=i) for i in range(31)]
    df_data = {"Appli": sorted(st.session_state.apps)}
    
    for d in dates:
        col_name = d.strftime("%d/%m")
        df_data[col_name] = []
        for app in df_data["Appli"]:
            cell_value = ""
            # Weekend ?
            if d.weekday() >= 5: cell_value = "WE"
            # Event ?
            for ev in st.session_state.events:
                if ev['app'] == app and ev['env'] == env_label:
                    if ev['d1'] <= d <= ev['d2']:
                        cell_value = ev['type']
            df_data[col_name].append(cell_value)

    df = pd.DataFrame(df_data)

    # Fonction de coloration des cellules (Pandas Styler)
    def apply_color(val):
        colors = {
            "MEP": "background-color: #0070C0; color: white",
            "Incident": "background-color: #FF0000; color: white",
            "Maintenance": "background-color: #FFC000; color: black",
            "Test": "background-color: #00B050; color: white",
            "Moratoire": "background-color: #9600C8; color: white",
            "WE": "background-color: #D9D9D9; color: transparent"
        }
        return colors.get(val, "background-color: white; color: transparent")

    # Affichage du tableau
    st.dataframe(
        df.style.applymap(apply_color),
        height=400,
        width=None, # stretch automatique
        hide_index=True
    )

# --- 4. INTERFACE ---
st.title("🚀 Planning IT - Version Ultra-Légère")

t1, t2, t3 = st.tabs(["PROD", "PRÉPROD", "RECETTE"])
with t1: style_planning("PROD")
with t2: style_planning("PRÉPROD")
with t3: style_planning("RECETTE")

