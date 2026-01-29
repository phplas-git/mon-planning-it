import streamlit as st
import pandas as pd
import calendar
from datetime import date

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# ==================================================
# SESSION STATE
# ==================================================
if "apps" not in st.session_state:
    st.session_state.apps = []

if "events" not in st.session_state:
    st.session_state.events = []

if "selected_cell" not in st.session_state:
    st.session_state.selected_cell = None

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:
    st.title("⚙️ Admin")

    # ---- Applications
    with st.form("add_app", clear_on_submit=True):
        new_app = st.text_input("Application").upper().strip()
        if st.form_submit_button("Ajouter") and new_app:
            if new_app not in st.session_state.apps:
                st.session_state.apps.append(new_app)
                st.rerun()

    st.divider()

    # ---- Events
    with st.form("add_event", clear_on_submit=True):
        if st.session_state.apps:
            f_app = st.selectbox("App", st.session_state.apps)
        else:
            st.info("Ajoutez d'abord une application")
            st.stop()

        f_env = st.selectbox("Env", ["PROD", "PRÉPROD", "RECETTE"])
        f_type = st.selectbox("Type", ["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"])
        f_comm = st.text_area("Détails")
        c1, c2 = st.columns(2)
        d1 = c1.date_input("Du")
        d2 = c2.date_input("Au")

        if st.form_submit_button("Enregistrer"):
            st.session_state.events.append({
                "app": f_app,
                "env": f_env,
                "type": f_type,
                "d1": d1,
                "d2": d2,
                "comment": f_comm
            })
            st.success("Événement enregistré")
            st.rerun()

# ==================================================
# MAIN
# ==================================================
st.title("📅 Planning IT – 2026")
env_selected = st.radio("Vue :", ["PROD", "PRÉPROD", "RECETTE"], horizontal=True)

months = [
    "Janvier","Février","Mars","Avril","Mai","Juin",
    "Juillet","Août","Septembre","Octobre","Novembre","Décembre"
]
tabs = st.tabs(months)

# ==================================================
# STYLE
# ==================================================
def style_val(val):
    styles = {
        "MEP": "background-color:#0070C0;color:white;font-weight:bold",
        "INC": "background-color:#FF0000;color:white;font-weight:bold",
        "MAI": "background-color:#FFC000;color:black;font-weight:bold",
        "TES": "background-color:#00B050;color:white;font-weight:bold",
        "MOR": "background-color:#9600C8;color:white;font-weight:bold",
        "•": "background-color:#f0f0f0;color:transparent"
    }
    return styles.get(val, "")

# ==================================================
# TABLES PAR MOIS
# ==================================================
for i, tab in enumerate(tabs):
    with tab:
        year = 2026
        month = i + 1
        nb_days = calendar.monthrange(year, month)[1]
        dates = [date(year, month, d) for d in range(1, nb_days + 1)]

        if not st.session_state.apps:
            st.info("Ajoutez une application pour commencer.")
            continue

        # ---- Construction data
        apps = sorted(st.session_state.apps)
        data = {"App": apps}

        for d in dates:
            col = str(d.day)
            data[col] = []
            for app in apps:
                val = "•" if d.weekday() >= 5 else ""
                for ev in st.session_state.events:
                    if ev["app"] == app and ev["env"] == env_selected:
                        if ev["d1"] <= d <= ev["d2"]:
                            val = ev["type"][:3]
                data[col].append(val)

        df = pd.DataFrame(data)

        # ---- Data editor (lecture seule)
        key_editor = f"editor_{env_selected}_{i}"

        st.data_editor(
            df.style.applymap(style_val),
            hide_index=True,
            disabled=True,
            key=key_editor
        )

        # ==================================================
        # SÉLECTION
        # ==================================================
        selected = st.session_state.get(key_editor, {}).get("selected_cells", [])

        if selected:
            cell = selected[0]
            row_idx = cell["row"]
            col_name = cell["column"]

            if col_name != "App":
                sel_app = df.iloc[row_idx]["App"]
                sel_day = int(col_name)
                sel_date = date(year, month, sel_day)

                st.divider()
                st.subheader(f"🔍 {sel_app} — {sel_day} {months[i]}")

                found = False
                for ev in st.session_state.events:
                    if ev["app"] == sel_app and ev["env"] == env_selected:
                        if ev["d1"] <= sel_date <= ev["d2"]:
                            found = True
                            with st.container(border=True):
                                st.metric("TYPE", ev["type"])
                                st.markdown(
                                    f"📅 **Du {ev['d1'].strftime('%d/%m')} "
                                    f"au {ev['d2'].strftime('%d/%m')}**"
                                )
                                if ev["comment"]:
                                    st.info(ev["comment"])
                                else:
                                    st.caption("Pas de commentaire.")

                if not found:
                    st.caption("Rien de prévu ce jour-là.")
        else:
            st.caption("👆 Cliquez sur une cellule pour voir le détail.")
