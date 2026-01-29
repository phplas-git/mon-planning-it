import streamlit as st
import time

st.set_page_config(page_title="SOS Planning", layout="wide")

st.title("🧪 Test Diagnostic - SOS Planning")

# On affiche l'heure pour voir si ça boucle (si les secondes défilent seules)
st.write(f"Heure actuelle du serveur : {time.strftime('%H:%M:%S')}")

if 'compteur' not in st.session_state:
    st.session_state.compteur = 0
if 'apps' not in st.session_state:
    st.session_state.apps = []

st.write(f"Nombre de rafraîchissements : {st.session_state.compteur}")
st.session_state.compteur += 1

st.divider()

# Test d'ajout simple
with st.form("test_form"):
    nom = st.text_input("Nom de l'appli test")
    submit = st.form_submit_button("Ajouter")
    
    if submit:
        st.session_state.apps.append(nom)
        st.success(f"Ajouté : {nom}")

st.write("Liste des applis en mémoire :")
st.write(st.session_state.apps)

