import streamlit as st

st.set_page_config(page_title="RScore Landing", page_icon="📊", layout="centered")

def show_landing():
    st.markdown("""
    <style>
    body { background-color: #f9fafb; }
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
    .card-link {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-decoration: none !important;
        background: white;
        border: 2px solid #e5e7eb;
        border-radius: 1rem;
        padding: 1.5rem;
        height: 210px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        transition: all .15s ease-in-out;
        text-align: center;
    }
    .card-link:hover {
        transform: scale(1.03);
        border-color: #6366F1;
        box-shadow: 0 10px 25px rgba(99,102,241,0.15);
    }
    .card-link h3 {
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: .3rem;
        color: #111827;
    }
    .card-link p {
        color: #374151;
        font-size: .95rem;
        margin: 0;
    }
    /* PRO CARD special styling */
    .pro-card {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
        color: white;
        border: none;
        box-shadow: 0 10px 25px rgba(99,102,241,0.25);
    }
    .pro-card h3, .pro-card p { color: white; }
    .pro-card:hover {
        transform: scale(1.05);
        box-shadow: 0 15px 35px rgba(79,70,229,0.4);
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

    # --- Equal sized, centered cards ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <a href="/Main" target="_self" class="card-link">
                <h3>Free Tools</h3>
                <p>Manual entry<br>R-score calculation<br>Min/max settings</p>
            </a>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <a href="/Main" target="_self" class="card-link pro-card">
                <h3>Pro</h3>
                <p>OCR import<br>Autofill credits<br>Program comparisons</p>
            </a>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="card-link" style="cursor:default;">
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

show_landing()
