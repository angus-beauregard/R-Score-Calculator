import streamlit as st
import pandas as pd
import numpy as np

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="R-Score Dashboard (Free)", layout="wide")

# ---------- HANDLE "UPGRADE" QUERY ----------
# If user clicks the HTML link ?upgrade=1 we set premium and jump to main app
qp = st.query_params
if "upgrade" in qp:
    st.session_state.is_premium = True
    st.session_state.onboarded = True
    # adjust this to the real main/pro app filename
    st.switch_page("app.py")

# ---------- BASE STYLES ----------
st.markdown(
    """
    <style>
    .top-banner {
        background: #e5edf7;
        border: 1px solid #d1ddf0;
        border-radius: 14px;
        padding: .7rem 1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .top-banner-text {
        color: #1f2a44;
        font-size: .9rem;
    }
    .upgrade-btn {
    background: #ffffff;
    border: 1.5px solid rgba(99,102,241,0.4);
    border-radius: 9999px;
    padding: 0.45rem 1.2rem 0.5rem 1.2rem;
    color: #4F46E5;
    font-weight: 600;
    font-size: 0.9rem;
    text-decoration: none !important;   /* removes underline */
    white-space: nowrap;
    box-shadow: 0 3px 6px rgba(0,0,0,0.05);
    transition: all 0.15s ease-in-out;
}
.upgrade-btn:hover {
    background: #4F46E5;
    color: #ffffff !important;
    transform: scale(1.03);
    box-shadow: 0 6px 12px rgba(99,102,241,0.25);
}
    }
    /* inline upgrade link for locked tabs */
    .inline-upgrade {
        display: inline-block;
        margin-top: .7rem;
        background: #4F46E5;
        color: #fff !important;
        text-decoration: none !important;
        padding: .35rem .85rem;
        border-radius: 9999px;
        font-size: .8rem;
        font-weight: 500;
    }
    # --- REMOVE SIDEBAR + 3-DOT MENU + HEADER ---
/* Hide hamburger menu, Streamlit header, and footer */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* Hide sidebar */
[data-testid="stSidebar"] {
    display: none;
}

/* Expand content to full width */
.block-container {
    padding-top: 1rem;
    padding-left: 3rem;
    padding-right: 3rem;
    max-width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown(
    '<h2 style="margin-bottom:0.2rem;">R-Score Dashboard (Free)</h2>'
    '<p style="color:#6b7280;margin-top:0;">Manual entry, basic R-score calculation, and settings.</p>',
    unsafe_allow_html=True,
)

# ---------- TOP BANNER (NO STREAMLIT BUTTON) ----------
st.markdown(
    """
    <div class="top-banner">
        <div class="top-banner-text">
            You’re on the free version. CSV, OCR, importance, and programs are premium.
        </div>
        <a href="?upgrade=1" class="upgrade-btn">✨ Upgrade to Premium</a>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- TABS ----------
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

# make sure we have a df
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(
        columns=["Course Name", "Your Grade", "Class Avg", "Std. Dev", "Credits"]
    )


def locked_tab():
    st.markdown("### 🔒 Premium feature")
    st.write("This section is part of the Pro version.")
    st.markdown('<a href="?upgrade=1" class="inline-upgrade">Upgrade to Premium</a>', unsafe_allow_html=True)


# -------- Help tab (free) --------
with tab_help:
    st.subheader("How to use the free version")
    st.write(
        "- Add courses in **Manual**\n"
        "- See your R-score in **Results**\n"
        "- Premium tabs stay visible so people know what Pro adds."
    )

# -------- Manual tab (free) --------
with tab_manual:
    st.write("Enter or edit your courses below.")
    base_df = st.session_state.df.copy()
    needed = ["Course Name", "Your Grade", "Class Avg", "Std. Dev", "Credits"]
    for c in needed:
        if c not in base_df.columns:
            base_df[c] = ""
    # data_editor is fine – user needs to edit somehow
    edited = st.data_editor(
        base_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
    )
    # no streamlit button; just auto-save on edit
    st.session_state.df = edited

# -------- CSV tab (locked) --------
with tab_csv:
    locked_tab()

# -------- Import tab (locked) --------
with tab_import:
    locked_tab()

# -------- Results tab (free) --------
with tab_results:
    df = st.session_state.df.copy()
    if df.empty:
        st.warning("No data yet. Add courses in the **Manual** tab.")
    else:
        # clean
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

        st.markdown(f"### Your R (central): **{overall_r:.2f}**")
        st.dataframe(
            df[["Course Name", "Your Grade", "Class Avg", "Std. Dev", "Credits", "R (central)"]],
            use_container_width=True,
        )

# -------- Importance tab (locked) --------
with tab_importance:
    locked_tab()

# -------- Biggest gains tab (locked) --------
with tab_gains:
    locked_tab()

# -------- Programs tab (locked) --------
with tab_programs:
    locked_tab()

# -------- Settings tab (free) --------
with tab_settings:
    locked_tab()
