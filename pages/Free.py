# pages/Free.py
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="RScore – Free", layout="wide")

# ---------- helper to block premium ----------
def require_premium():
    st.markdown("### 🔒 Premium feature")
    st.write("This section is available in the Pro version. Go back to the landing page and choose **Pro** to unlock it.")
    st.stop()

st.markdown(
    '<h2 style="margin-bottom:0.2rem;">R-Score Dashboard (Free)</h2>'
    '<p style="color:#6b7280;margin-top:0;">Manual entry, calculation, settings.</p>',
    unsafe_allow_html=True
)

# ---------- tabs ----------
# these are the tabs you already have in Main.py — we mark some as premium
tab_help, tab_manual, tab_csv, tab_import, tab_results, tab_importance, tab_gains, tab_programs, tab_settings = st.tabs([
    "Help / Explanation",
    "Manual",
    "CSV",
    "Import (OCR) 🔒",
    "Results",
    "Importance 🔒",
    "Biggest gains 🔒",
    "Programs 🔒",
    "Settings",
])

# ----- HELP (free) -----
with tab_help:
    st.subheader("How to use the free version")
    st.write(
        "- Enter courses manually in the **Manual** tab\n"
        "- Upload a CSV in **CSV** (optional)\n"
        "- See your R-score in **Results**\n"
        "- Premium tabs are shown but locked so you know what you’d get."
    )

# make sure there is a df in session
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Course Name", "Your Grade", "Class Avg", "Std. Dev", "Credits"])

# ----- MANUAL (free) -----
with tab_manual:
    st.write("Enter or edit your courses below. This is free.")
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

# ----- CSV (free) -----
with tab_csv:
    st.write("Upload a CSV with the columns: Course Name, Your Grade, Class Avg, Std. Dev, Credits.")
    up = st.file_uploader("Upload CSV", type=["csv"])
    if up is not None:
        try:
            df_up = pd.read_csv(up)
            for c in ["Course Name", "Your Grade", "Class Avg", "Std. Dev", "Credits"]:
                if c not in df_up.columns:
                    df_up[c] = np.nan
            st.session_state.df = df_up
            st.success(f"Loaded {len(df_up)} rows.")
        except Exception as e:
            st.error(f"CSV error: {e}")

# ----- IMPORT (premium) -----
with tab_import:
    require_premium()

# ----- RESULTS (free) -----
with tab_results:
    df = st.session_state.df.copy()
    if df.empty:
        st.warning("No data yet.")
    else:
        # clean numerics
        for c in ["Your Grade", "Class Avg", "Std. Dev", "Credits"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["Credits"] = df["Credits"].fillna(1)
        df.loc[df["Credits"] == 0, "Credits"] = 1

        def zscore(row):
            g, a, s = row["Your Grade"], row["Class Avg"], row["Std. Dev"]
            if pd.isna(g) or pd.isna(a) or pd.isna(s) or s == 0:
                return 0.0
            return (g - a) / s

        df["Z"] = df.apply(zscore, axis=1)
        df["R (central)"] = 35 + 5 * df["Z"]
        total_credits = df["Credits"].sum()
        if total_credits <= 0:
            total_credits = 1
        overall_r = (df["R (central)"] * df["Credits"]).sum() / total_credits

        st.metric("R (central)", f"{overall_r:.2f}")
        st.dataframe(df[["Course Name", "Your Grade", "Class Avg", "Std. Dev", "Credits", "R (central)"]], use_container_width=True)

# ----- IMPORTANCE (premium) -----
with tab_importance:
    require_premium()

# ----- BIGGEST GAINS (premium) -----
with tab_gains:
    require_premium()

# ----- PROGRAMS (premium) -----
with tab_programs:
    require_premium()

# ----- SETTINGS (free) -----
with tab_settings:
    st.write("You can put your min / max offsets here in free too, or just leave defaults.")
    min_off = st.number_input("R offset (min)", value=-2.0, step=0.5)
    max_off = st.number_input("R offset (max)", value=2.0, step=0.5)
    st.caption("Premium version could let you save and track history of these.")
