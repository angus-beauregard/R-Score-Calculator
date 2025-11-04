import streamlit as st

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
        display: block;
        text-decoration: none;
        background: white;
        border: 2px solid #e5e7eb;
        border-radius: 1rem;
        padding: 1.2rem;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        transition: all .15s ease-in-out;
        text-align: left;
        height: 100%;
    }
    .card-link:hover {
        transform: scale(1.03);
        border-color: #6366F1;
        box-shadow: 0 10px 25px rgba(99,102,241,0.15);
    }
    .card-link h3 {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: .3rem;
        color: #111827;
    }
    .card-link p {
        color: #374151;
        font-size: .95rem;
        margin: 0;
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

    # --- Cards section ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <a href="https://7y59cdkurbzlm96a3xon9w.streamlit.app/" target="_blank" class="card-link">
                <h3>Free Tools</h3>
                <p>Manual entry, R-score calculation, and min/max settings.</p>
            </a>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <a href="https://7y59cdkurbzlm96a3xon9w.streamlit.app/" target="_blank" class="card-link" style="background:#eef2ff;border-color:#6366F1;">
                <h3>Pro (Mock)</h3>
                <p>OCR import, autofill credits, program comparisons.</p>
            </a>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="card-link" style="pointer-events:none;">
                <h3>Why trust it?</h3>
                <p>Runs entirely in your browser<br>No Omnivox credentials<br>Formula shown</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="footer-mini">RScore Pro © 2025 • Not affiliated with John Abbott College or Omnivox.</div>',
        unsafe_allow_html=True,
    )


# ===== MAIN LANDING =====
show_landing()
