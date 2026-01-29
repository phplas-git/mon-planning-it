import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Planning IT Pro", layout="wide")

if 'apps' not in st.session_state:
    st.session_state.apps = []
if 'events' not in st.session_state:
    st.session_state.events = []

st.title("📅 Planning IT - Vue Calendrier")

# --- 2. BARRE LATÉRALE ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    d_start = st.date_input("Date de début", date(2026, 1, 1))
    nb_jours = st.slider("Nombre de jours", 14, 60, 30)
    
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
        if f_app:
            st.session_state.events.append({
                'app': f_app, 'env': f_env, 'type': f_type, 'd1': f_d1, 'd2': f_d2
            })
            st.success("Enregistré !")
            st.rerun()
    
    st.divider()
    if st.button("🗑️ Réinitialiser tout"):
        st.session_state.apps, st.session_state.events = [], []
        st.rerun()

# --- 3. LOGIQUE DU PLANNING ---
def build_planning(env_name):
    if not st.session_state.apps:
        st.info("Ajoutez une application à gauche.")
        return

    # Jours de la semaine en français
    jours_fr = ["L", "M", "M", "J", "V", "S", "D"]
    dates = [d_start + timedelta(days=i) for i in range(nb_jours)]
    
    apps_sorted = sorted(st.session_state.apps)
    rows = []
    
    for app in apps_sorted:
        row = {"Application": app}
        for d in dates:
            # Entête : MOIS | Jour Num | Initiale Jour
            col_name = f"{d.strftime('%b').upper()} | {d.strftime('%d')} {jours_fr[d.weekday()]}"
            
            # Détermination du contenu de la cellule
            cell_val = ""
            if d.weekday() >= 5: cell_val = "WE"
            
            for ev in st.session_state.events:
                if ev['app'] == app and ev['env'] == env_name:
                    if ev['d1'] <= d <= ev['d2']:
                        # On met le texte en abrégé pour la lisibilité
                        cell_val = ev['type'][:3].upper() 
            
            row[col_name] = cell_val
        rows.append(row)

    df = pd.DataFrame(rows)

    # --- 4. STYLISATION AVANCÉE ---
    def style_cells(val):
        # Couleurs de fond
        bg = "transparent"
        txt = "transparent" # On cache le texte sauf si c'est un event
        weight = "normal"
        
        if val == "MEP": bg, txt, weight = "#0070C0", "white", "bold"
        elif val == "INC": bg, txt, weight = "#FF0000", "white", "bold"
        elif val == "MAI": bg, txt, weight = "#FFC000", "black", "bold"
        elif val == "TES": bg, txt, weight = "#00B050", "white", "bold"
        elif val == "MOR": bg, txt, weight = "#9600C8", "white", "bold"
        elif val == "WE": bg, txt = "#262730", "#555" # Gris foncé pour le WE
        
        return f'background-color: {bg}; color: {txt}; font-weight: {weight}; border: 0.1px solid #444'

    st.dataframe(
        df.style.applymap(style_cells),
        use_container_width=True,
        height=(len(apps_sorted) + 2) * 38,
        hide_index=True
    )

# --- 5. INTERFACE ---
# Légende visuelle
st.markdown("""
<div style="display: flex; gap: 10px; margin-bottom: 20px; font-size: 12px;">
    <div style="padding: 2px 8px; background: #0070C0; color: white; border-radius: 4px;">MEP</div>
    <div style="padding: 2px 8px; background: #FF0000; color: white; border-radius: 4px;">INCIDENT</div>
    <div style="padding: 2px 8px; background: #FFC000; color: black; border-radius: 4px;">MAINTENANCE</div>
    <div style="padding: 2px 8px; background: #00B050; color: white; border-radius: 4px;">TEST</div>
    <div style="padding: 2px 8px; background: #9600C8; color: white; border-radius: 4px;">MORATOIRE</div>
</div>
""", unsafe_allow_html=True)

t1, t2, t3 = st.tabs(["💻 PROD", "🧪 PRÉPROD", "🛠️ RECETTE"])
with t1: build_planning("PROD")
with t2: build_planning("PRÉPROD")
with t3: build_planning("RECETTE")
