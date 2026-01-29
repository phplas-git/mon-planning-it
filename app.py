import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta, date

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Planning IT Ultra-Stable", layout="wide")

# INITIALISATION DE LA MÉMOIRE (Session State)
# On crée nos "tables" virtuelles dans la RAM du navigateur
if 'apps' not in st.session_state:
    st.session_state.apps = []
if 'events' not in st.session_state:
    st.session_state.events = []

# --- 2. BARRE LATÉRALE ---
with st.sidebar:
    st.title("⚙️ Configuration")
    
    d_start = st.date_input("Vue à partir du", date(2026, 1, 1))
    days_show = st.slider("Jours à afficher", 30, 120, 60)
    
    st.divider()
    
    with st.expander("📝 Gérer les Applications"):
        new_a = st.text_input("Nom de l'appli").upper()
        if st.button("Ajouter"):
            if new_a and new_a not in st.session_state.apps:
                st.session_state.apps.append(new_a)
                st.toast(f"Appli {new_a} ajoutée !")
            elif new_a in st.session_state.apps:
                st.warning("Déjà dans la liste")
    
    st.divider()
    
    st.subheader("➕ Nouvel événement")
    with st.form("form_ajout", clear_on_submit=True):
        f_app = st.selectbox("Sélectionner l'Appli", st.session_state.apps)
        f_env = st.selectbox("Environnement", ["PROD", "PRÉPROD", "RECETTE"])
        f_type = st.selectbox("Type", ["MEP", "Incident", "Maintenance", "Test", "Moratoire"])
        f_d1 = st.date_input("Date de début")
        f_d2 = st.date_input("Date de fin")
        
        if st.form_submit_button("Valider"):
            if f_app:
                # On ajoute à notre liste en mémoire
                st.session_state.events.append({
                    'app': f_app, 'env': f_env, 'type': f_type, 
                    'd1': f_d1.isoformat(), 'd2': f_d2.isoformat()
                })
                st.success("Événement enregistré !")

# --- 3. LOGIQUE D'AFFICHAGE ---
def draw_grid(env_label):
    if not st.session_state.apps:
        st.warning(f"⚠️ Aucune application. Ajoutez-en une à gauche.")
        return

    # On récupère les données depuis la mémoire
    apps = sorted(st.session_state.apps, reverse=True)
    df_ev = pd.DataFrame(st.session_state.events)
    
    # Filtrage par environnement
    if not df_ev.empty:
        df_ev = df_ev[df_ev['env'] == env_label]
    
    dates_list = [d_start + timedelta(days=x) for x in range(days_show)]
    grid = np.zeros((len(apps), len(dates_list)))
    hover_matrix = []
    
    t_val = {"MEP": 1, "Incident": 2, "Maintenance": 3, "Test": 4, "Moratoire": 5}
    
    for i, app in enumerate(apps):
        row_hover = []
        for j, d in enumerate(dates_list):
            val = 0
            txt = f"<b>{app}</b><br>{d.strftime('%d/%m/%Y')}"
            if d.weekday() >= 5:
                val = 6
                txt += " (WE)"
            
            if not df_ev.empty:
                d_str = d.isoformat()
                match = df_ev[(df_ev['app'] == app) & (df_ev['d1'] <= d_str) & (df_ev['d2'] >= d_str)]
                if not match.empty:
                    val = t_val.get(match.iloc[0]['type'], 0)
                    txt += f"<br>TYPE: {match.iloc[0]['type']}"
            
            grid[i, j] = val
            row_hover.append(txt)
        hover_matrix.append(row_hover)

    colors = ["#FFFFFF", "#0070C0", "#FF0000", "#FFC000", "#00B050", "#9600C8", "#D9D9D9"]
    fig = px.imshow(grid, x=[d.strftime("%d\n%b") for d in dates_list], y=apps,
                    color_continuous_scale=colors, zmin=0, zmax=6, aspect="auto")

    fig.update_traces(hovertemplate="%{customdata}<extra></extra>", customdata=hover_matrix)
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(side="top", showgrid=True, gridwidth=1, gridcolor='black', dtick=1)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='black', dtick=1)
    
    today = date.today()
    if d_start <= today <= (d_start + timedelta(days=days_show)):
        idx = (today - d_start).days
        fig.add_vline(x=idx, line_width=2, line_dash="dash", line_color="#FF4B4B")

    fig.update_layout(height=180 + (len(apps) * 35), margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, width='stretch', key=f"grid_{env_label}", config={'displayModeBar': False})

# --- 4. INTERFACE ---
st.title("🚀 Planning IT - Mode Ultra-Stable")

l_cols = st.columns(6)
legende = [("MEP","#0070C0"), ("Incident","#FF0000"), ("Maint.","#FFC000"), ("Test","#00B050"), ("Mora.","#9600C8"), ("WE","#D9D9D9")]
for i, (n, c) in enumerate(legende):
    l_cols[i].markdown(f'<div style="display:flex;align-items:center;"><div style="width:12px;height:12px;background:{c};border:1px solid #000;margin-right:5px;"></div><span style="font-size:11px;">{n}</span></div>', unsafe_allow_html=True)

t_prod, t_pre, t_rec = st.tabs(["PROD", "PRÉPROD", "RECETTE"])
with t_prod: draw_grid("PROD")
with t_pre: draw_grid("PRÉPROD")
with t_rec: draw_grid("RECETTE")
