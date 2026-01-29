import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Planning IT Stable", layout="wide")

# Initialisation de la mémoire (RAM)
if 'apps' not in st.session_state:
    st.session_state.apps = []
if 'events' not in st.session_state:
    st.session_state.events = []

st.title("📅 Planning IT - Vue Tabulaire")

# --- 2. BARRE LATÉRALE ---
with st.sidebar:
    st.header("⚙️ Configuration")
    d_start = st.date_input("Date de début", date(2026, 1, 1))
    nb_jours = st.number_input("Nombre de jours", min_value=7, max_value=60, value=30)
    
    st.divider()
    
    # Export de secours
    if st.session_state.events:
        df_export = pd.DataFrame(st.session_state.events)
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Exporter les données (CSV)", data=csv, file_name="planning_backup.csv", mime="text/csv")
        if st.button("🗑️ Tout effacer"):
            st.session_state.apps = []
            st.session_state.events = []
            st.rerun()

    st.divider()
    
    with st.expander("📝 Applications"):
        new_a = st.text_input("Nom de l'appli").upper()
        if st.button("Ajouter"):
            if new_a and new_a not in st.session_state.apps:
                st.session_state.apps.append(new_a)
                st.rerun()

    st.subheader("➕ Nouvel événement")
    f_app = st.selectbox("Application", [""] + sorted(st.session_state.apps))
    f_env = st.selectbox("Environnement", ["PROD", "PRÉPROD", "RECETTE"])
    f_type = st.selectbox("Type", ["MEP", "Incident", "Maintenance", "Test", "Moratoire"])
    f_d1 = st.date_input("Du")
    f_d2 = st.date_input("Au")
    if st.button("Enregistrer"):
        if f_app != "":
            st.session_state.events.append({
                'app': f_app, 'env': f_env, 'type': f_type, 'd1': f_d1, 'd2': f_d2
            })
            st.success("Enregistré !")
            st.rerun()

# --- 3. LOGIQUE DE LA GRILLE ---
def build_planning(env_name):
    if not st.session_state.apps:
        st.info("Ajoutez une application dans la barre latérale.")
        return

    # Création de l'axe des temps
    dates = [d_start + timedelta(days=i) for i in range(nb_jours)]
    
    # Préparation des lignes (une par appli)
    rows = []
    apps_sorted = sorted(st.session_state.apps)
    
    for app in apps_sorted:
        row = {"Application": app}
        for d in dates:
            col_name = d.strftime("%d/%m")
            # Valeur par défaut
            cell_val = " " 
            if d.weekday() >= 5: cell_val = "WE"
            
            # Match des événements
            for ev in st.session_state.events:
                if ev['app'] == app and ev['env'] == env_name:
                    if ev['d1'] <= d <= ev['d2']:
                        cell_val = ev['type']
            
            row[col_name] = cell_val
        rows.append(row)

    df = pd.DataFrame(rows)

    # --- 4. STYLISATION DES COULEURS ---
    def style_cells(val):
        bg = "white"
        txt = "black"
        if val == "MEP": bg, txt = "#0070C0", "white"
        elif val == "Incident": bg, txt = "#FF0000", "white"
        elif val == "Maintenance": bg, txt = "#FFC000", "black"
        elif val == "Test": bg, txt = "#00B050", "white"
        elif val == "Moratoire": bg, txt = "#9600C8", "white"
        elif val == "WE": bg, txt = "#EEEEEE", "#EEEEEE" # WE presque invisible
        
        if val == " ": bg = "white"
        return f'background-color: {bg}; color: {txt}; border: 0.1px solid #f0f0f0'

    # Affichage
    st.dataframe(
        df.style.applymap(style_cells),
        use_container_width=True,
        height=(len(apps_sorted) + 1) * 36,
        hide_index=True
    )

# --- 5. INTERFACE ---
t1, t2, t3 = st.tabs(["PROD", "PRÉPROD", "RECETTE"])
with t1: build_planning("PROD")
with t2: build_planning("PRÉPROD")
with t3: build_planning("RECETTE")
