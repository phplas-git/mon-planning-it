import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date

st.set_page_config(page_title="IT Roadmap Pro", layout="wide")

# Données de test pour voir le rendu immédiatement
if 'events' not in st.session_state:
    st.session_state.events = [
        dict(App="PRAC", Start='2026-01-01', Finish='2026-01-10', Type="MEP", Env="PROD"),
        dict(App="RACING", Start='2026-01-15', Finish='2026-01-20', Type="Incident", Env="PROD")
    ]

st.title("🚀 IT Roadmap & Planning - 2026")

# --- FILTRES ---
with st.sidebar:
    st.header("🔍 Filtres & Saisie")
    f_env = st.selectbox("Environnement", ["PROD", "PRÉPROD", "RECETTE"])
    st.divider()
    
    with st.form("Ajout"):
        st.subheader("➕ Nouvel événement")
        app = st.text_input("Application").upper()
        t_ev = st.selectbox("Type", ["MEP", "Incident", "Maintenance", "Test", "Moratoire"])
        d1 = st.date_input("Début")
        d2 = st.date_input("Fin")
        if st.form_submit_button("Ajouter au planning"):
            if app:
                st.session_state.events.append(dict(App=app, Start=d1.isoformat(), Finish=d2.isoformat(), Type=t_ev, Env=f_env))
                st.rerun()

# --- AFFICHAGE GANTT ---
if st.session_state.events:
    df = pd.DataFrame(st.session_state.events)
    df = df[df['Env'] == f_env] # Filtrage par onglet/bouton

    if not df.empty:
        # Création du graphique de Timeline (Gantt)
        fig = px.timeline(df, 
                          x_start="Start", 
                          x_end="Finish", 
                          y="App", 
                          color="Type",
                          color_discrete_map={
                              "MEP": "#0070C0", "Incident": "#FF0000", 
                              "Maintenance": "#FFC000", "Test": "#00B050", "Moratoire": "#9600C8"
                          },
                          hover_data=["Type"])
        
        fig.update_yaxes(autorange="reversed") # Les nouvelles apps en haut
        fig.update_layout(
            xaxis_title="Calendrier 2026",
            yaxis_title="Applications",
            height=400,
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Ajout du sélecteur de date (Zoom)
        fig.update_xaxes(rangeslider_visible=True)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"Aucun événement pour {f_env}")
