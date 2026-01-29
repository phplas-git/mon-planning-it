import streamlit as st
import pandas as pd
import calendar
from datetime import date

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
st.set_page_config(page_title="Planning IT Pro", layout="wide")

# --------------------------------------------------
# SESSION STATE INIT
# --------------------------------------------------
if "apps" not in st.session_state:
    st.session_state.apps = []

if "events" not in st.session_state:
    st.session_state.events = []

if "selected_cell" not in st.session_state:
    st.session_state.selected_cell = None

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.title("⚙️ Admin")

    # ---- Applications
    with st.form("new_app_form", clear_on_submit=True):
        st.subheader("Applications")
        new_app = st.text_input("Nom").upper().strip()
        if st.form_submit_button("Ajouter"):
            if new_app and new_app not in st.session_state.apps:
                st.session_state.apps.append(new_app)
                st.rerun()

    st.divider()

    # ---- Events
    st.subheader("Nouvel événement")
    apps_list = sorted(st.session_state.apps) if st.session_state.apps else [""]

    with st.form("event_form", clear_on_submit=True):
        f_app = st.selectbox("App", apps_list)
        f_env = st.selectbox("Env", ["PROD", "PRÉPROD", "RECETTE"])
        f_type = st.selectbox("Type", ["MEP", "INCIDENT", "MAINTENANCE", "TEST", "MORATOIRE"])
        f_comm = st.text_area("Détails")

        c1, c2 = st.columns(2)
        d1 = c1.date_input("Du")
        d2 = c2.date_input("Au")

        if st.form_submit_button("Enregistrer") and f_app:
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

    if st.button("Tout effacer"):
        st.session_state.apps = []
        st.session_state.events = []
        st.session_state.selected_cell = None
        st.rerun()

# --------------------------------------------------
# MAIN
# --------------------------------------------------
st.title("📅 Planning IT – 2026")
env_selected = st.radio("Vue :", ["PROD", "PRÉPROD", "RECETTE"], horizontal=True)

mois = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]
tabs = st.tabs(mois)

# --------------------------------------------------
# STYLE
# --------------------------------------------------
def style_val(val):
    styles = {
        "MEP": "background-color:#0070C0;color:white;font-weight:bold",
        "INC": "background-color:#FF0000;color:white;font-weight:bold",
        "MAI": "background-color:#FFC000;color:black;font-weight:bold",
        "TES": "background-color:#00B050;color:white;font-weight:bold",
        "MOR": "background-color:#9600C8;color:white;font-weight:bold",
        "•": "background-color:#f4f4f4;color:transparent"
    }
    return styles.get(val, "")

# --------------------------------------------------
# TABLES PAR MOIS
# --------------------------------------------------
for i, tab in enumerate(tabs):
    with tab:
        if not st.session_state.apps:
            st.info("Ajoutez une application pour commencer.")
            continue

        year = 2026
        month = i + 1
        last_day = calendar.monthrange(year, month)[1]
        dates = [date(year, month, d) for d in range(1, last_day + 1)]

        apps = sorted(st.session_state.apps)
        data = {"App": apps}

        # ---- Construction des cellules
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

        # ---- Colonnes
        cf = {"App": st.column_config.TextColumn("App", pinned=True)}
        for d in dates:
            cf[str(d.day)] = st.column_config.TextColumn(str(d.day), width=35)

        # ---- Dataframe
        key_df = f"grid_{env_selected}_{year}_{i}"

        st.dataframe(
            df.style.applymap(style_val),
            use_container_width=True,
            hide_index=True,
            column_config=cf,
            selection_mode=["single-row", "single-column"],
            key=key_df
        )

        # ---- Lecture sélection (API correcte)
        selection = st.session_state.get(key_df, {}).get("selection", {})
        rows = selection.get("rows", [])
        cols = selection.get("columns", [])

        if rows and cols:
            st.session_state.selected_cell = {
                "month": i,
                "row": rows[0],
                "col": cols[0],
                "env": env_selected
            }

        # --------------------------------------------------
        # DÉTAIL ÉVÉNEMENT
        # --------------------------------------------------
        sel = st.session_state.selected_cell
        if sel and sel["month"] == i and sel["env"] == env_selected:
            col_name = sel["col"]
            row_idx = sel["row"]

            if col_name != "App":
                sel_app = apps[row_idx]
                sel_day = int(col_name)
                sel_date = date(year, month, sel_day)

                st.divider()
                st.subheader(f"🔍 {sel_app} — {sel_day} {mois[i]}")

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
