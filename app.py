import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import numpy as np
import os
from datetime import datetime, timedelta, date

# --- 1. CONFIGURATION DU CHEMIN HORS PROJET ---
st.set_page_config(page_title="Planning IT Stable", layout="wide")

# On place la base de données dans ton dossier "Documents" pour que Streamlit ne la voie pas
# Cela évite la boucle infinie car le fichier n'est plus dans le dossier PlanningEnv
home_dir = os.path.expanduser("~")
DB_PATH = os.path.join(home_dir, "planning_it_data.db")

def query_db(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if fetch:
            res = cursor.fetchall()
            return res
        conn.commit()
    finally:
        conn.close()

# Initialisation
query_db('CREATE TABLE IF NOT EXISTS apps (nom TEXT UNIQUE)')
query_db('CREATE TABLE IF NOT EXISTS events (app TEXT, env TEXT, type TEXT, d1 TEXT, d2 TEXT)')

# --- 2. BARRE LATÉRALE ---
st.sidebar.title("⚙️ Paramètres")
d_start = st.sidebar.date_input("Vue à partir du", date(2026, 1, 1))
days_show = st.sidebar.slider("Jours à afficher", 30, 120, 60)

with st.sidebar.expander("📝 Gérer les Applications"):
    new_a = st.text_input("Nom de l'appli").upper()
    if st.button("Ajouter l'Appli"):
        if new_a:
            query_db("INSERT OR IGNORE INTO apps (nom) VALUES (?)", (new_a,))
            st.success("Ajouté ! Faites F5")

st.sidebar.divider()
apps_data = query_db("SELECT nom FROM apps ORDER BY nom", fetch=True)
list_apps = [r[0] for r in apps_data] if apps_data else []

st.sidebar.subheader("➕ Nouvel événement")
with st.sidebar.form("form_add", clear_on_submit=True):
    f_app = st.selectbox("Application", list_apps)
    f_env = st.selectbox("Env", ["PROD", "PRÉPROD", "RECETTE"])
    f_type = st.selectbox("Type", ["MEP", "Incident", "Maintenance", "Test", "Moratoire"])
    f_d1 = st.date_input("Début")
    f_d2 = st.date_input("Fin")
    if st.form_submit_button("Enregistrer"):
        if f_app:
            query_db("INSERT INTO events VALUES (?,?,?,?,?)", 
                     (f_app, f_env, f_type, f_d1.isoformat(), f_d2.isoformat()))
            st.success("Enregistré ! Faites F5")

# --- 3. AFFICHAGE ---
st.title("🚀 Mon Planning IT")
c_map = {"MEP":"#0070C0", "Incident":"#FF0000", "Maintenance":"#FFC000", "Test":"#00B050", "Moratoire":"#9600C8", "WE":"#D9D9D9"}
cols = st.columns(len(c_map))
for i, (name, col) in enumerate(c_map.items()):
    cols[i].markdown(f'<div style="background:{col};height:10px;border:1px solid #000;"></div><p style="font-size:10px;text-align:center;">{name}</p>', unsafe_allow_html=True)

def draw_grid(env_label):
    apps_data = query_db("SELECT nom FROM apps ORDER BY nom DESC", fetch=True)
    if not apps_data:
        st.info("Aucune application.")
        return
    
    apps = [r[0] for r in apps_data]
    events_data = query_db("SELECT * FROM events WHERE env=?", (env_label,), fetch=True)
    df = pd.DataFrame(events_data, columns=['app','env','type','d1','d2']) if events_data else pd.DataFrame()
    
    dates = [d_start + timedelta(days=x) for x in range(days_show)]
    grid = np.zeros((len(apps), len(dates)))
    t_val = {"MEP": 1, "Incident": 2, "Maintenance": 3, "Test": 4, "Moratoire": 5}
    
    for i, app in enumerate(apps):
        for j, d in enumerate(dates):
            val = 0
            if d.weekday() >= 5: val = 6
            if not df.empty:
                d_str = d.isoformat()
                match = df[(df['app'] == app) & (df['d1'] <= d_str) & (df['d2'] >= d_str)]
                if not match.empty:
                    val = t_val.get(match.iloc[0]['type'], 0)
            grid[i, j] = val

    fig = px.imshow(grid, x=[d.strftime("%d\n%b") for d in dates], y=apps,
                    color_continuous_scale=["#FFFFFF", "#0070C0", "#FF0000", "#FFC000", "#00B050", "#9600C8", "#D9D9D9"],
                    zmin=0, zmax=6, aspect="auto")
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(side="top", showgrid=True, gridwidth=1, gridcolor='black', dtick=1)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='black', dtick=1)
    fig.update_layout(height=150+(len(apps)*30), margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True, key=f"gr_{env_label}", config={'displayModeBar': False})

t1, t2, t3 = st.tabs(["PROD", "PRÉPROD", "RECETTE"])
with t1: draw_grid("PROD")
with t2: draw_grid("PRÉPROD")
with t3: draw_grid("RECETTE")