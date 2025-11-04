# ====== MOCK ACCESS / LANDING ======
if "onboarded" not in st.session_state:
    st.session_state.onboarded = False
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False

def show_landing():
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
    .hero-actions {
        margin-top: 1.5rem;
        display: flex;
        gap: .7rem;
        justify-content: center;
        flex-wrap: wrap;
    }
    .btn-primary {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
        color: white;
        border: none;
        border-radius: .75rem;
        padding: .65rem 1.5rem;
        font-weight: 600;
        cursor:pointer;
    }
    .btn-secondary {
        background: white;
        color: #111827;
        border: 1px solid rgba(15,23,42,0.06);
        border-radius: .75rem;
        padding: .55rem 1.2rem;
        cursor:pointer;
    }
    .feature-grid {
        margin-top: 2.5rem;
        display: grid;
        gap: 1rem;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    }
    .feat-card {
        background: rgba(255,255,255,0.55);
        border: 1px solid rgba(255,255,255,0.55);
        border-radius: 1.1rem;
        padding: 1rem 1rem 1.2rem 1rem;
        text-align: left;
        box-shadow: 0 10px 30px rgba(15,23,42,0.04);
    }
    .feat-title {
        font-weight: 600;
        margin-bottom: .25rem;
    }
    .footer-mini {
        margin-top: 2.5rem;
        text-align:center;
        font-size:.75rem;
        color:#9ca3af;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="hero-wrap glass-card">
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

        <div class="hero-actions">
            <form action="#" method="post">
                <button name="pro" class="btn-primary" onclick="document.dispatchEvent(new Event('pro'));return false;">Unlock Pro (mock)</button>
            </form>
            <form action="#" method="post">
                <button name="free" class="btn-secondary" onclick="document.dispatchEvent(new Event('free'));return false;">Continue with free tools</button>
            </form>
        </div>

        <div class="feature-grid">
            <div class="feat-card">
                <div class="feat-title">Free</div>
                <div>• Manual course entry<br>• R-score calculation<br>• Settings for min / max</div>
            </div>
            <div class="feat-card">
                <div class="feat-title">Pro (mock)</div>
                <div>• OCR Import from screenshots<br>• Autofill credits<br>• Program comparisons</div>
            </div>
            <div class="feat-card">
                <div class="feat-title">Why trust it?</div>
                <div>Runs in your browser, no Omnivox credentials, formula shown.</div>
            </div>
        </div>

        <div class="footer-mini">
            RScore Pro © 2025 • Not affiliated with John Abbott College or Omnivox.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # real buttons (Streamlit ones) so we can actually change state
    colA, colB = st.columns([1,1])
    with colA:
        if st.button("🚀 Unlock Pro (mock)"):
            st.session_state.is_premium = True
            st.session_state.onboarded = True
            st.rerun()
    with colB:
        if st.button("➡️ Continue with free tools"):
            st.session_state.onboarded = True
            st.rerun()

# if user hasn't chosen yet, show landing and stop
if not st.session_state.onboarded:
    show_landing()
    st.stop()
