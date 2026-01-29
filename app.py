import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta

# --- 1. STYLE & CONFIG ---
st.set_page_config(page_title="IT Planning Pro", layout="wide")

# CSS pour injecter un look "Tableau de Bord" (Bordures, couleurs, polices)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 1.5rem; }
    .stDataFrame { border: 1px solid #dee2e6; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

if 'events' not in st.session_state: st.session_state.events = []
if 'apps' not in st.session_state: st.session_state.apps = ["APP_TEST"]

# --- 2. BARRE LATÉRALE ---
with st.sidebar:
    st.title("🛡️ Admin Panel")
    with st.expander("🚀 Ajouter une Application"):
        new_app = st.text_input("Nom de l'app").upper()
        if st.button("Ajouter"):
            if new_app and new_app not in st.session_state.apps:
                st.session_state.apps.append(new_app)
                st.rerun()

    st.subheader("📝 Nouvel Événement")
    with st.form("add_event", clear_on_submit=True):
        f_app = st.selectbox("Application", sorted(st.session_state.apps))
        f_env = st.selectbox("Environnement", ["PROD", "PRÉPROD", "RECETTE"])
        f_type = st.selectbox("Type", ["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"])
        col1, col2 = st.columns(2)
        f_d1 = col1.date_input("Début")
        f_d2 = col2.date_input("Fin")
        if st.form_submit_button("Enregistrer"):
            st.session_state.events.append({'app': f_app, 'env': f_env, 'type': f_type, 'd1': f_d1, 'd2': f_d2})
            st.success("Ajouté !")

    if st.button("🗑️ Reset"):
        st.session_state.events, st.session_state.apps = [], ["APP_TEST"]
        st.rerun()

# --- 3. LOGIQUE D'AFFICHAGE PAR MOIS ---
st.title("📅 Planning Industriel IT - 2026")

# Choix de l'environnement en haut
env_selected = st.radio("Secteur :", ["PROD", "PRÉPROD", "RECETTE"], horizontal=True)

# Création des onglets pour chaque mois de l'année
mois_noms = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
tabs = st.tabs(mois_noms)

for i, tab in enumerate(tabs):
    with tab:
        month_num = i + 1
        year = 2026
        
        # Nombre de jours dans le mois
        num_days = calendar.monthrange(year, month_num)[1]
        dates = [date(year, month_num, d) for d in range(1, num_days + 1)]
        
        # Construction de la grille
        if not st.session_state.apps:
            st.warning("Aucune application configurée.")
        else:
            apps = sorted(st.session_state.apps)
            grid_data = {"Applications": apps}
            
            for d in dates:
                # En-tête : Jour (L, M, M...)
                day_name = calendar.day_name[d.weekday()][0].upper()
                col_name = f"{d.day} {day_name}"
                
                grid_data[col_name] = []
                for app in apps:
                    val = ""
                    if d.weekday() >= 5: val = "•" # Marqueur weekend
                    
                    # Vérification des événements
                    for ev in st.session_state.events:
                        if ev['app'] == app and ev['env'] == env_selected:
                            if ev['d1'] <= d <= ev['d2']:
                                val = ev['type']
                    grid_data[col_name].append(val)
            
            df = pd.DataFrame(grid_data)

            # --- STYLISATION DES COULEURS ---
            def color_excel(val):
                color = ""
                if val == "MEP": color = "background-color: #0070C0; color: white; font-weight: bold"
                elif val == "INCIDENT": color = "background-color: #FF0000; color: white; font-weight: bold"
                elif val == "MAINTENANCE": color = "background-color: #FFC000; color: black; font-weight: bold"
                elif val == "TEST": color = "background-color: #00B050; color: white; font-weight: bold"
                elif val == "MORATOIRE": color = "background-color: #9600C8; color: white; font-weight: bold"
                elif val == "•": color = "background-color: #f1f3f4; color: #bdc1c6" # Style WE
                return color

            st.dataframe(df.style.applymap(color_excel), use_container_width=True, hide_index=True)

# --- 4. LÉGENDE ---
st.divider()
st.markdown("""
    <div style="display: flex; gap: 20px; justify-content: center;">
        <span style="color: #0070C0;">● MEP</span>
        <span style="color: #FF0000;">● INCIDENT</span>
        <span style="color: #FFC000;">● MAINTENANCE</span>
        <span style="color: #00B050;">● TEST</span>
        <span style="color: #9600C8;">● MORATOIRE</span>
    </div>
    """, unsafe_allow_html=True)
