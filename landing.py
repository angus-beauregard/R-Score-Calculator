import streamlit as st

# ====== BASIC STATE ======
if "onboarded" not in st.session_state:
    st.session_state.onboarded = False
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False


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
.card {
    background: #fff;
    border-radius: 1rem;
    box-shadow: 0 8px 25px rgba(0,0,0,0.05);
    padding: 1.25rem;
    height: 100%;
}
.card h3 {
    margin-top: 0;
    font-size: 1.1rem;
    color: #111827;
}
.card p {
    color: #374151;
    font-size: .95rem;
    line-height: 1.5;
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

    # Real Streamlit layout and buttons
    col_free, col_pro, col_trust = st.columns(3)

    with col_free:
        st.markdown('<div class="card"><h3>Free Tools</h3><p>• Manual course entry<br>• R-score calculation<br>• Settings for min / max</p></div>', unsafe_allow_html=True)
        if st.button("➡️ Continue with free tools"):
            st.session_state.onboarded = True
            st.session_state.is_premium = False
            st.rerun()

    with col_pro:
        st.markdown('<div class="card"><h3>Pro (mock)</h3><p>• OCR import from screenshots<br>• Autofill credits<br>• Program comparisons</p></div>', unsafe_allow_html=True)
        if st.button("🚀 Unlock Pro (mock)"):
            st.session_state.onboarded = True
            st.session_state.is_premium = True
            st.rerun()

    with col_trust:
        st.markdown('<div class="card"><h3>Why trust it?</h3><p>Runs entirely in your browser.<br>No Omnivox credentials required.<br>Formula shown transparently.</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="footer-mini">RScore Pro © 2025 • Not affiliated with John Abbott College or Omnivox.</div>', unsafe_allow_html=True)


# ====== GATE ======
if not st.session_state.onboarded:
    show_landing()
    st.stop()

# ====== MAIN APP ======
st.title("R-Score Dashboard")
st.write(f"Welcome to {'RScore Pro' if st.session_state.is_premium else 'RScore Free'} mode!")
# continue with your main tabs / calculator here...
