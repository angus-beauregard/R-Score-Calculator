import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="RScore – Free", layout="wide")

# simple helper for locked tabs
def locked_tab():
    st.markdown("### 🔒 Premium feature")
    st.write("This section is part of the Pro version.")
    # upgrade button
    if st.button("✨ Upgrade to Premium"):
        # FUTURE: send user to Stripe checkout; on success, set these:
        st.session_state.is_premium = True
        # you can also set a flag to tell the main app to open directly
        st.session_state.onboarded = True
        # then send them to the main/pro page
        st.switch_page("app.py")  # adjust to your actual main file name

st.markdown(
    '<h2 style="margin-bottom:0.2rem;">R-Score Dashboard (Free)</h2>'
    '<p style="color:#6b7280;margin-top:0;">Manual entry, basic R-score calculation, and settings.</p>',
    unsafe_allow_html=True
)

# ===== UPGRADE BAR AT THE TOP =====
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("You’re on the free version. CSV, OCR, importance, and programs are premium.")
    with col2:
        if st.button("✨ Upgrade to Premium", use_container_width=True):
            # FUTURE: redirect to Stripe
            st.session_state.is_premium = True
            st.session_state.onboarded = True
            st.switch_page("app.py")  # adjust to your main app filename

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
        "- Premium tabs show you what you’d unlock."
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

# 3) CSV (locked)
with tab_csv:
    locked_tab()

# 4) IMPORT (locked)
with tab_import:
    locked_tab()

# 5) RESULTS (free)
with tab_results:
    df = st.session_state.df.copy()
    if df.empty:
        st.warning("No data yet. Add courses in the **Manual** tab.")
    else:
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
    locked_tab()

# 7) BIGGEST GAINS (locked)
with tab_gains:
    locked_tab()

# 8) PROGRAMS (locked)
with tab_programs:
    locked_tab()

# 9) SETTINGS (locker)
with tab_settings:
    locked_tab()
