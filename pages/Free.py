# pages/Free.py
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="RScore – Free", layout="wide")

def show_locked_tab():
    st.markdown("### 🔒 Premium feature")
    st.write("This section is part of the Pro version. Upgrade on the landing page to unlock it.")

st.markdown(
    '<h2 style="margin-bottom:0.2rem;">R-Score Dashboard (Free)</h2>'
    '<p style="color:#6b7280;margin-top:0;">Manual entry, basic R-score calculation, and settings.</p>',
    unsafe_allow_html=True
)

tabs = st.tabs([
    "Help / Explanation",
    "Manual",
    "CSV 🔒",
    "Import (OCR) 🔒",
    "Results",
    "Importance 🔒",
    "Biggest gains 🔒",
    "Programs 🔒",
    "Settings",
])
(
    tab_help,
    tab_manual,
    tab_csv,
    tab_import,
    tab_results,
    tab_importance,
    tab_gains,
    tab_programs,
    tab_settings,
) = tabs

# ensure df exists
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Course Name", "Your Grade", "Class Avg", "Std. Dev", "Credits"])

# 1) HELP
with tab_help:
    st.subheader("How to use the free version")
    st.write(
        "- Add courses in **Manual**\n"
        "- See your R-score in **Results**\n"
        "- CSV / OCR / analysis tabs are locked here so users see what Pro adds."
    )

# 2) MANUAL (free)
with tab_manual:
    st.write("Enter or edit your courses below.")
    base_df = st.session_state.df.copy()
    needed = ["Course Name", "Your Grade", "Class Avg", "Std. Dev", "Credits"]
    for c in needed:
        if c not in base_df.columns:
            base_df[c] = ""
    edited = st.data_editor(
        base_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
    )
    if st.button("✅ Save changes (free)"):
        st.session_state.df = edited
        st.success("Saved.")

# 3) CSV (locked, but no st.stop)
with tab_csv:
    show_locked_tab()

# 4) IMPORT (locked)
with tab_import:
    show_locked_tab()

# 5) RESULTS (free)
with tab_results:
    df = st.session_state.df.copy()
    if df.empty:
        st.warning("No data yet. Add courses in the **Manual** tab.")
    else:
        # numeric cleanup
        for c in ["Your Grade", "Class Avg", "Std. Dev", "Credits"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["Credits"] = df["Credits"].fillna(1)
        df.loc[df["Credits"] == 0, "Credits"] = 1

        def zscore_row(row):
            g, a, s = row["Your Grade"], row["Class Avg"], row["Std. Dev"]
            if pd.isna(g) or pd.isna(a) or pd.isna(s) or s == 0:
                return 0.0
            return (g - a) / s

        df["Z"] = df.apply(zscore_row, axis=1)
        df["R (central)"] = 35 + 5 * df["Z"]

        total_credits = df["Credits"].sum() or 1
        overall_r = (df["R (central)"] * df["Credits"]).sum() / total_credits

        st.metric("R (central)", f"{overall_r:.2f}")
        st.dataframe(
            df[["Course Name", "Your Grade", "Class Avg", "Std. Dev", "Credits", "R (central)"]],
            use_container_width=True,
        )

# 6) IMPORTANCE (locked)
with tab_importance:
    show_locked_tab()

# 7) BIGGEST GAINS (locked)
with tab_gains:
    show_locked_tab()

# 8) PROGRAMS (locked)
with tab_programs:
    show_locked_tab()

# 9) SETTINGS (free)
with tab_settings:
    st.subheader("R-range settings (free)")
    r_min = st.number_input("R offset (min)", value=-2.0, step=0.5)
    r_max = st.number_input("R offset (max)", value=2.0, step=0.5)
    st.caption("These don’t change the per-course formula (35 + 5×Z), but in Pro you could use them for ranges.")
