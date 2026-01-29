import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import numpy as np
import os
from datetime import datetime, timedelta, date

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# Petit message de test pour voir si le site répond
st.toast("Connexion au serveur réussie !", icon="🚀")

# Utilisation du dossier /tmp pour la stabilité sur le Cloud
DB_PATH = "/tmp/planning_it_2026.db"

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

# Initialisation des tables
query_db('CREATE TABLE IF NOT EXISTS apps (nom TEXT UNIQUE)')
query_db('CREATE TABLE IF NOT EXISTS events (app TEXT, env TEXT, type TEXT, d1 TEXT, d2 TEXT)')

# --- 2. BARRE LATÉRALE ---
with st.sidebar:
    st.title("⚙️ Configuration")
    d_start = st.date_input("Vue à partir du", date(2026, 1, 1))
    days_show = st.slider("Jours à afficher", 30, 120, 60)
    
    st.divider()
    
    with st.expander("📝 Gérer les Applications"):
        new_a = st.text_input("Nom de l'appli").upper()
        if st.button("Enregistrer l'Appli"):
            if new_a:
                query_db("INSERT OR IGNORE INTO apps (nom) VALUES (?)", (new_a,))
                st.success(f"{new_a} ajouté !")
                st.rerun()
    
    st.divider()
    
    st.subheader("➕ Nouvel événement")
    apps_data = query_db("SELECT nom FROM apps ORDER BY nom", fetch=True)
    list_apps = [r[0] for r in apps_data] if apps_data else []
    
    with st.form("form_ajout", clear_on_submit=True):
        f_app = st.selectbox("Application", list_apps)
        f_env = st.selectbox("Environnement", ["PROD", "PRÉPROD", "RECETTE"])
        f_type = st.selectbox("Type", ["MEP", "Incident", "Maintenance", "Test", "Moratoire"])
        f_d1 = st.date_input("Début")
        f_d2 = st.date_input("Fin")
        
        if st.form_submit_button("Valider"):
            if f_app:
                query_db("INSERT INTO events VALUES (?,?,?,?,?)", 
                         (f_app, f_env, f_type, f_d1.isoformat(), f_d2.isoformat()))
                st.success("Événement enregistré !")
                st.rerun()

# --- 3. AFFICHAGE DE LA GRILLE ---
def draw_grid(env_label):
    apps_db = query_db("SELECT nom FROM apps ORDER BY nom DESC", fetch=True)
    if not apps_db:
        st.info("Utilisez la barre latérale pour ajouter vos applications.")
        return
    
    apps = [r[0] for r in apps_db]
    events_db = query_db("SELECT * FROM events WHERE env=?", (env_label,), fetch=True)
    df_ev = pd.DataFrame(events_db, columns=['app','env','type','d1','d2']) if events_db else pd.DataFrame()
    
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
                txt += " (Weekend)"
            
            if not df_ev.empty:
                d_str = d.isoformat()
                match = df_ev[(df_ev['app'] == app) & (df_ev['d1'] <= d_str) & (df_ev['d2'] >= d_str)]
                if not match.empty:
                    val = t_val.get(match.iloc[0]['type'], 0)
                    txt += f"<br><b>{match.iloc[0]['type']}</b>"
            
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
    
    # Aujourd'hui
    today = date.today()
    if d_start <= today <= (d_start + timedelta(days=days_show)):
        idx = (today - d_start).days
        fig.add_vline(x=idx, line_width=2, line_dash="dash", line_color="#FF4B4B")

    fig.update_layout(height=150 + (len(apps) * 35), margin=dict(l=0, r=0, t=20, b=0))
    # Correction suggérée par tes logs : width='stretch'
    st.plotly_chart(fig, width='stretch', key=f"grid_{env_label}", config={'displayModeBar': False})

# --- 4. INTERFACE ---
st.title("🚀 Planning IT - 2026")

l_cols = st.columns(6)
legende_items = [("MEP","#0070C0"), ("Incident","#FF0000"), ("Maintenance","#FFC000"), 
                 ("Test","#00B050"), ("Moratoire","#9600C8"), ("Weekend","#D9D9D9")]
for i, (n, c) in enumerate(legende_items):
    l_cols[i].markdown(f'<div style="display:flex;align-items:center;"><div style="width:12px;height:12px;background:{c};border:1px solid #000;margin-right:5px;"></div><span style="font-size:11px;">{n}</span></div>', unsafe_allow_html=True)

t_prod, t_pre, t_rec = st.tabs(["PROD", "PRÉPROD", "RECETTE"])
with t_prod: draw_grid("PROD")
with t_pre: draw_grid("PRÉPROD")
with t_rec: draw_grid("RECETTE")
