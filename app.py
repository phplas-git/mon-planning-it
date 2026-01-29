import streamlit as st
import pandas as pd
import calendar
from datetime import date

# --- CONFIGURATION ---
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# --- VÉRIFICATION AUTOMATIQUE DE LA VERSION ---
# Si le serveur est trop vieux, on affiche une alerte rouge
v_maj = int(st.__version__.split('.')[1])
if v_maj < 35:
    st.error(f"⚠️ VERSION OBSOLÈTE DÉTECTÉE ({st.__version__}). Le clic ne marchera pas.")
    st.info("👉 Veuillez mettre à jour votre fichier 'requirements.txt' sur GitHub avec : streamlit==1.41.1")
    st.stop() # On arrête tout pour éviter le crash moche

# --- INITIALISATION ---
if 'events' not in st.session_state: st.session_state.events = []
if 'apps' not in st.session_state: st.session_state.apps = []

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title("⚙️ Admin")
    
    # Ajout App
    with st.form("new_app_form", clear_on_submit=True):
        st.subheader("Applications")
        new_app = st.text_input("Nom").upper().strip()
        if st.form_submit_button("Ajouter") and new_app:
            if new_app not in st.session_state.apps:
                st.session_state.apps.append(new_app)
                st.rerun()

    st.divider()
    
    # Ajout Event
    st.subheader("Nouvel Événement")
    if not st.session_state.apps:
        st.warning("Ajoutez une app d'abord.")
    else:
        with st.form("event_form", clear_on_submit=True):
            f_app = st.selectbox("App", sorted(st.session_state.apps))
            f_env = st.selectbox("Env", ["PROD", "PRÉPROD", "RECETTE"])
            f_type = st.selectbox("Type", ["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"])
            f_comm = st.text_area("Détails")
            c1, c2 = st.columns(2)
            d1 = c1.date_input("Du")
            d2 = c2.date_input("Au")
            
            if st.form_submit_button("Enregistrer"):
                st.session_state.events.append({
                    'app': f_app, 'env': f_env, 'type': f_type, 
                    'd1': d1, 'd2': d2, 'comment': f_comm
                })
                st.success("Enregistré !")
                st.rerun()
                
    if st.button("Tout effacer"):
        st.session_state.apps, st.session_state.events = [], []
        st.rerun()

# --- MAIN ---
st.title("📅 Planning IT - Interactif")
env_selected = st.radio("Vue :", ["PROD", "PRÉPROD", "RECETTE"], horizontal=True)

mois = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
tabs = st.tabs(mois)

# Style (Compatible Pandas 2.x grâce à requirements.txt)
def style_val(val):
    colors = {
        "MEP": "background-color: #0070C0; color: white; font-weight: bold",
        "INC": "background-color: #FF0000; color: white; font-weight: bold",
        "MAI": "background-color: #FFC000; color: black; font-weight: bold",
        "TES": "background-color: #00B050; color: white; font-weight: bold",
        "MOR": "background-color: #9600C8; color: white; font-weight: bold",
        "•": "background-color: #f8f9fa; color: transparent"
    }
    return colors.get(val, "")

for i, tab in enumerate(tabs):
    with tab:
        month = i + 1
        year = 2026
        last_day = calendar.monthrange(year, month)[1]
        dates = [date(year, month, d) for d in range(1, last_day + 1)]
        
        if st.session_state.apps:
            apps = sorted(st.session_state.apps)
            data = {"App": apps}
            
            for d in dates:
                col = str(d.day)
                data[col] = []
                for app in apps:
                    val = ""
                    if d.weekday() >= 5: val = "•"
                    for ev in st.session_state.events:
                        if ev['app'] == app and ev['env'] == env_selected:
                            if ev['d1'] <= d <= ev['d2']:
                                val = ev['type'][:3]
                    data[col].append(val)
            
            df = pd.DataFrame(data)

            # Config Colonnes
            cf = {"App": st.column_config.TextColumn("App", pinned=True)}
            for d in dates:
                cf[str(d.day)] = st.column_config.TextColumn(str(d.day), width=35)

            # --- TABLEAU CLIQUABLE ---
            response = st.dataframe(
                df.style.map(style_val),
                use_container_width=True,
                hide_index=True,
                column_config=cf,
                on_select="rerun",  # C'EST ICI QUE LA MAGIE OPÈRE
                selection_mode=["single_row", "single_column"] # Mode cellule
            )
            
            # --- INTERACTION ---
            # On vérifie si l'utilisateur a cliqué
            if response.selection.rows and response.selection.columns:
                r_idx = response.selection.rows[0]
                c_name = response.selection.columns[0]
                
                # Si on ne clique pas sur la colonne du nom de l'app
                if c_name != "App":
                    sel_app = apps[r_idx]
                    sel_day = int(c_name)
                    sel_date = date(year, month, sel_day)
                    
                    st.divider()
                    st.subheader(f"🔍 Détail : {sel_app} (Le {sel_day} {mois[i]})")
                    
                    # On cherche l'event
                    found = False
                    for ev in st.session_state.events:
                        if ev['app'] == sel_app and ev['env'] == env_selected:
                            if ev['d1'] <= sel_date <= ev['d2']:
                                found = True
                                with st.container(border=True):
                                    c1, c2 = st.columns([1,4])
                                    c1.metric("TYPE", ev['type'])
                                    c2.markdown(f"📅 **Du {ev['d1'].strftime('%d/%m')} au {ev['d2'].strftime('%d/%m')}**")
                                    if ev['comment']:
                                        c2.info(f"📝 {ev['comment']}")
                                    else:
                                        c2.caption("Pas de commentaire.")
                    
                    if not found:
                        st.info("Aucun événement prévu sur cette case.")
            else:
                st.caption("👆 Cliquez sur une case pour voir le détail.")
