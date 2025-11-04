import streamlit as st

# ====== BASIC STATE ======
if "onboarded" not in st.session_state:
    st.session_state.onboarded = False
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False


def clickable_card(label, title, description, key, color="#ffffff", border="#e5e7eb"):
    """Reusable clickable box styled as a button"""
    clicked = st.button(
        label=label,
        key=key,
        help=title,
        use_container_width=True,
    )
    st.markdown(
        f"""
        <style>
        div[data-testid="stButton"][key="{key}"] button {{
            all: unset;
            width: 100%;
            height: 100%;
            display: block;
            cursor: pointer;
            background: {color};
            border: 2px solid {border};
            border-radius: 1rem;
            padding: 1.2rem;
            text-align: left;
            box-shadow: 0 5px 20px rgba(0,0,0,0.04);
            transition: all .15s ease-in-out;
        }}
        div[data-testid="stButton"][key="{key}"] button:hover {{
            transform: scale(1.02);
            box-shadow: 0 8px 25px rgba(0,0,0,0.08);
            border-color: #6366F1;
        }}
        div[data-testid="stButton"][key="{key}"] button p {{
            margin: 0;
            color: #374151;
            font-size: .95rem;
        }}
        div[data-testid="stButton"][key="{key}"] button h3 {{
            margin-top: 0;
            font-size: 1.1rem;
            font-weight: 600;
            color: #111827;
            margin-bottom: .3rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    return clicked


def show_landing():
    # top hero
    st.markdown("""
    <style>
    .hero-wrap {
        max-width: 960px;
        margin: 0 auto;
        padding: 2.5rem 1.5rem 2rem 1.5rem;
        text-align: center;
    }
    .hero-title {
        font-size: clamp(2.3rem, 4vw, 2.8rem);
        font-weight: 700;
        color: #111827;
        letter-spacing: -0.03em;
    }
    .hero-sub {
        margin-top: 1rem;
        font-size: 1rem;
        color: #4b5563;
    }
    .hero-badges {
        margin-top: 1.2rem;
        display: flex;
        gap: .6rem;
        justify-content: center;
        flex-wrap: wrap;
    }
    .hero-badge {
        background: rgba(79,70,229,0.08);
        border: 1px solid rgba(79,70,229,0.15);
        color: #1f2937;
        padding: .35rem .7rem;
        border-radius:9999px;
        font-size:.7rem;
    }
    .footer-mini {
        margin-top: 2.5rem;
        text-align:center;
        font-size:.75rem;
        color:#9ca3af;
    }
    </style>

    <div class="hero-wrap">
        <div style="display:flex;justify-content:center;margin-bottom:1rem;">
            <div style="background:rgba(99,102,241,.12);padding:.35rem .75rem;border-radius:9999px;font-size:.7rem;color:#4f46e5;">
                RScore Pro • Quebec CEGEP R-score helper
            </div>
        </div>
        <div class="hero-title">Your R-Score, cleaned up.</div>
        <div class="hero-sub">Import Omnivox screenshots, autofill credits, see admission ranges, and track scenarios. Manual entry stays free.</div>

        <div class="hero-badges">
            <div class="hero-badge">✓ No Omnivox password stored</div>
            <div class="hero-badge">✓ Uses standard 35 + 5 × Z</div>
            <div class="hero-badge">✓ Built for JAC students</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # interactive cards
    col1, col2, col3 = st.columns(3)

    with col1:
        if clickable_card(
            "Free Tools",
            "Free Tools",
            "Manual entry, R-score calculation, and min/max adjustments.",
            "free_card",
        ):
            st.session_state.onboarded = True
            st.session_state.is_premium = False
            st.rerun()

    with col2:
        if clickable_card(
            "Pro (Mock)",
            "Pro (Mock)",
            "OCR import, autofill credits, program comparisons.",
            "pro_card",
            color="#eef2ff",
            border="#6366F1",
        ):
            st.session_state.onboarded = True
            st.session_state.is_premium = True
            st.rerun()

    with col3:
        st.markdown(
            """
            <div style="background:white;border-radius:1rem;padding:1.2rem;
            border:2px solid #e5e7eb;box-shadow:0 5px 20px rgba(0,0,0,0.04);height:100%;">
            <h3>Why trust it?</h3>
            <p>Runs fully in your browser<br>No Omnivox credentials<br>Formula shown</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="footer-mini">RScore Pro © 2025 • Not affiliated with John Abbott College or Omnivox.</div>',
        unsafe_allow_html=True,
    )


# ====== ACCESS GATE ======
if not st.session_state.onboarded:
    show_landing()
    st.stop()

# ====== MAIN APP ======
st.title("R-Score Dashboard")
st.write(f"Welcome to {'RScore Pro' if st.session_state.is_premium else 'RScore Free'} mode!")
# (Insert your calculator tabs here)
