import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import numpy as np
import os
from datetime import datetime, timedelta, date

# --- 1. CONFIGURATION ET STABILITÉ ---
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# Chemin vers la base de données (Le dossier /tmp est ignoré par le "surveilleur" Streamlit)
DB_PATH = "/tmp/planning_it_2026.db"

def query_db(query, params=(), fetch=False):
    """Gère la connexion à la base de données de manière isolée."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        conn.commit()
    finally:
        conn.close()

# Initialisation des tables (IF NOT EXISTS pour éviter les erreurs)
query_db('CREATE TABLE IF NOT EXISTS apps (nom TEXT UNIQUE)')
query_db('CREATE TABLE IF NOT EXISTS events (app TEXT, env TEXT, type TEXT, d1 TEXT, d2 TEXT)')

# --- 2. BARRE LATÉRALE (CONFIGURATION & SAISIE) ---
with st.sidebar:
    st.title("⚙️ Paramètres")
    d_start = st.date_input("Vue à partir du", date(2026, 1, 1))
    days_show = st.slider("Nombre de jours à afficher", 30, 120, 60)
    
    st.divider()
    
    # Section Gestion des Applications
    with st.expander("📝 Gérer les Applications"):
        new_a = st.text_input("Ajouter une application").upper()
        if st.button("Enregistrer l'Appli"):
            if new_a:
                query_db("INSERT OR IGNORE INTO apps (nom) VALUES (?)", (new_a,))
                st.success(f"Appli {new_a} ajoutée !")
                st.rerun() #
