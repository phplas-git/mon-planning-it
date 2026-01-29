import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# DEBUG : Affiche la version pour qu'on sache ce qui tourne
st.write(f"Version du système : Streamlit {st.__version__}")

# Initialisation
if 'events' not in st.session_state: st.session_state.events = []
if 'apps' not in st.session_state: st.session_state.apps = []

# --- 2. BARRE LATÉRALE ---
with st.sidebar:
    st.title("⚙️ Admin")
    
    # Ajout App simplissime
    st.subheader("Ajouter une App")
    new_app = st.text_input("Nom", key="new_app_input").upper().strip()
    if st.button("Ajouter"):
        if new_app and new_app not in st.session_state.apps:
            st.session_state.apps.append(new_app)
            st.rerun()

    st.divider()
    
    # Ajout Event
    st.subheader("Nouvel Événement")
    if not st.session_state.apps:
        st.warning("Ajoutez une app d'abord.")
    else:
        with st.form("event_form"):
            f_app = st.selectbox("App", sorted(st.session_state.apps))
            f_env = st.selectbox("Env", ["PROD", "PRÉPROD", "RECETTE"])
            f_type = st.selectbox("Type", ["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"])
            f_comm = st.text_area("Détails")
            c1, c2 = st.columns(2)
            d1 = c1.date_input("Du")
            d2 = c2.date_input("Au")
            
            if st.form_submit_button("Sauvegarder"):
                st.session_state.events.append({
                    'app': f_app, 'env': f_env, 'type': f_type, 
                    'd1': d1, 'd2': d2, 'comment': f_comm
                })
                st.success("OK")
                st.rerun()
                
    if st.button("Reset Total"):
        st.session_state.apps = []
        st.session_state.events = []
        st.rerun()

# --- 3. AFFICHAGE ---
st.title("📅 Planning IT - 2026")
env_selected = st.radio("Vue :", ["PROD", "PRÉPROD", "RECETTE"], horizontal=True)

mois = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
tabs = st.tabs(mois)

# Fonction couleur compatible toutes versions Pandas
def style_val(v):
    if v == "MEP": return "background-color: #0070C0; color: white"
    if v == "INC": return "background-color: #FF0000; color: white"
    if v == "MAI": return "background-color: #FFC000; color: black"
    if v == "TES": return "background-color: #00B050; color: white"
    if v == "MOR": return "background-color: #9600C8; color: white"
    if v == "•": return "background-color: #eee; color: #eee"
    return ""

for i, tab in enumerate(tabs):
    with tab:
        month = i + 1
        year = 2026
        last_day = calendar.monthrange(year, month)[1]
        dates = [date(year, month, d) for d in range(1, last_day + 1)]
        
        if not st.session_state.apps:
            st.info("Liste vide.")
        else:
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

            # Configuration simple des colonnes
            cf = {"App": st.column_config.TextColumn("App", pinned=True)}
            for d in dates:
                cf[str(d.day)] = st.column_config.TextColumn(str(d.day), width=35)

            # Affichage SANS interaction de clic (Source d'erreur supprimée)
            # On utilise applymap qui marche sur les vieilles versions de Pandas aussi
            try:
                st.dataframe(
                    df.style.applymap(style_val),
                    use_container_width=True,
                    hide_index=True,
                    column_config=cf
                )
            except:
                # Fallback ultime si applymap plante
                st.dataframe(df, use_container_width=True, hide_index=True)

            # --- SÉLECTEUR MANUEL POUR LES DÉTAILS ---
            st.divider()
            col_sel, col_det = st.columns([1, 3])
            
            with col_sel:
                st.markdown("#### 🔍 Loupe")
                target_app = st.selectbox(f"Voir détails en {mois[i]} pour :", ["-- Choisir --"] + apps, key=f"sel_{i}")
            
            with col_det:
                if target_app and target_app != "-- Choisir --":
                    found = False
                    for ev in st.session_state.events:
                        if ev['app'] == target_app and ev['env'] == env_selected:
                            # Si l'événement touche ce mois-ci
                            if (ev['d1'].month == month or ev['d2'].month == month):
                                found = True
                                with st.container(border=True):
                                    st.markdown(f"**{ev['type']}** | Du {ev['d1'].strftime('%d/%m')} au {ev['d2'].strftime('%d/%m')}")
                                    if ev['comment']:
                                        st.info(f"{ev['comment']}")
                    if not found:
                        st.caption("Rien ce mois-ci pour cette application.")
