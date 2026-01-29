import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import numpy as np
import os
from datetime import datetime, timedelta, date

# --- 1. CONFIGURATION DU SERVEUR ---
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# Dossier temporaire pour éviter la boucle infinie sur le Cloud
DB_PATH = "/tmp/planning_2026_v2.db"

def query_db(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        conn.commit()
    finally:
        conn.close()

# Initialisation silencieuse
query_db('CREATE TABLE IF NOT EXISTS apps (nom TEXT UNIQUE)')
query_db('CREATE TABLE IF NOT EXISTS events (app TEXT, env TEXT, type TEXT, d1 TEXT, d2 TEXT)')

# --- 2. BARRE LATÉRALE ---
with st.sidebar:
    st.title("⚙️ Configuration")
    d_start = st.date_input("Vue à partir du", date(2026, 1, 1))
    days_show = st.sidebar.slider("Jours à afficher", 30, 120, 60)
    
    st.divider()
    
    with st.expander("📝 Gérer les Applications"):
        new_a = st.text_input("Nom de l'appli (ex: PRAC)").upper()
        if st.button("Enregistrer l'Appli"):
            if new_a:
                query_db("INSERT OR IGNORE INTO apps (nom) VALUES (?)", (new_a,))
                st.success(f"Appli {new_a} ajoutée !")
                st.rerun()
    
    st.divider()
    
    # Récupération des applis pour le formulaire
    apps_data = query_db("SELECT nom FROM apps ORDER BY nom", fetch=True)
    list_apps = [r[0] for r in apps_data] if apps_data else []
    
    st.subheader("➕ Nouvel événement")
    with st.form("form_ajout", clear_on_submit=True):
        f_app = st.selectbox("Sélectionner l'Appli", list_apps)
        f_env = st.selectbox("Environnement", ["PROD", "PRÉPROD", "RECETTE"])
        f_type = st.selectbox("Catégorie", ["MEP", "Incident", "Maintenance", "Test", "Moratoire"])
        f_d1 = st.date_input("Date de début")
        f_d2 = st.date_input("Date de fin")
        
        if st.form_submit_button("Valider"):
            if f_app:
                query_db("INSERT INTO events VALUES (?,?,?,?,?)", 
                         (f_app, f_env, f_type, f_d1.isoformat(), f_d2.isoformat()))
                st.success("Événement enregistré !")
                st.rerun()

# --- 3. LOGIQUE D'AFFICHAGE ---
def draw_grid(env_label):
    apps_db = query_db("SELECT nom FROM apps ORDER BY nom DESC", fetch=True)
    
    # Sécurité : Si aucune application, on affiche un message clair
    if not apps_db:
        st.warning(f"⚠️ Aucune application enregistrée pour la vue {env_label}. Ajoutez-en une dans la barre latérale.")
        return

    apps = [r[0] for r in apps_db]
    events_db = query_db("SELECT * FROM events WHERE env=?", (env_label,), fetch=True)
    df_ev = pd.DataFrame(events_db, columns=['app','env','type','d1','d2']) if events_db else pd.DataFrame()
    
    dates_list = [d_start + timedelta(days=x) for x in range(days_show)]
    grid = np.zeros((len(apps), len(dates_list)))
    hover_matrix = []

    # Couleurs : 0:Blanc, 1:MEP, 2:Incident, 3:Maint, 4:Test, 5:Mora, 6:Weekend
    t_val = {"MEP": 1, "Incident": 2, "Maintenance": 3, "Test": 4, "Moratoire": 5}
    
    for i, app in enumerate(apps):
        row_hover = []
        for j, d in enumerate(dates_list):
            val = 0
            txt = f"<b>{app}</b><br>{d.strftime('%d/%m/%Y')}"
            if d.weekday() >= 5:
                val = 6
                txt += " (Weekend)"
            
            if not df_ev.empty:
                d_str = d.isoformat()
                match = df_ev[(df_ev['app'] == app) & (df_ev['d1'] <= d_str) & (df_ev['d2'] >= d_str)]
                if not match.empty:
                    val = t_val.get(match.iloc[0]['type'], 0)
                    txt += f"<br>TYPE: {match.iloc[0]['type']}"
            
            grid[i, j] = val
            row_hover.append(txt)
        hover_matrix.append(row_hover)

    # Palette 2026
    colors = ["#FFFFFF", "#0070C0", "#FF0000", "#FFC000", "#00B050", "#9600C8", "#D9D9D9"]
    
    fig = px.imshow(grid, x=[d.strftime("%d\n%b") for d in dates_list], y=apps,
                    color_continuous_scale=colors, zmin=0, zmax=6, aspect="auto")

    fig.update_traces(hovertemplate="%{customdata}<extra></extra>", customdata=hover_matrix)
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(side="top", showgrid=True, gridwidth=1, gridcolor='black', dtick=1)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='black', dtick=1)
    
    # Marqueur "Aujourd'hui"
    today = date.today()
    if d_start <= today <= (d_start + timedelta(days=days_show)):
        idx = (today - d_start).days
        fig.add_vline(x=idx, line_width=2, line_dash="dash", line_color="#FF4B4B")

    # Correction de l'affichage Plotly pour 2026
    fig.update_layout(height=180 + (len(apps) * 35), margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, width='stretch', key=f"grid_{env_label}", config={'displayModeBar': False})

# --- 4. INTERFACE ---
st.title("🚀 Planning IT - 2026")
st.toast("Serveur prêt", icon="✅")

# Légende
l_cols = st.columns(6)
legende = [("MEP","#0070C0"), ("Incident","#FF0000"), ("Maint.","#FFC000"), ("Test","#00B050"), ("Mora.","#9600C8"), ("WE","#D9D9D9")]
for i, (n, c) in enumerate(legende):
    l_cols[i].markdown(f'<div style="display:flex;align-items:center;"><div style="width:12px;height:12px;background:{c};border:1px solid #000;margin-right:5px;"></div><span style="font-size:11px;">{n}</span></div>', unsafe_allow_html=True)

# Navigation par Onglets
tab_prod, tab_pre, tab_rec = st.tabs(["PROD", "PRÉPROD", "RECETTE"])
with tab_prod: draw_grid("PROD")
with tab_pre: draw_grid("PRÉPROD")
with tab_rec: draw_grid("RECETTE")
