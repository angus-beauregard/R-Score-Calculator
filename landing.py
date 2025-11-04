import streamlit as st

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
.feature-grid {
    margin-top: 2.5rem;
    display: grid;
    gap: 1rem;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}
.feat-card {
    background: rgba(255,255,255,0.65);
    border: 1px solid rgba(0,0,0,0.05);
    border-radius: 1.1rem;
    padding: 1.2rem;
    text-align: left;
    box-shadow: 0 10px 30px rgba(15,23,42,0.04);
}
.feat-title {
    font-weight: 600;
    margin-bottom: .25rem;
}
.feat-button {
    display: block;
    margin-top: .8rem;
    text-align: center;
    padding: .6rem 1rem;
    border-radius: .75rem;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
}
.btn-primary {
    background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
    color: white;
    border: none;
}
.btn-secondary {
    background: white;
    border: 1px solid rgba(15,23,42,0.08);
    color: #111827;
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

  <div class="feature-grid">
    <div class="feat-card">
      <div class="feat-title">Free Tools</div>
      <div>• Manual course entry<br>• R-score calculation<br>• Settings for min / max</div>
    </div>

    <div class="feat-card">
      <div class="feat-title">Pro (Mock)</div>
      <div>• OCR import from screenshots<br>• Autofill credits<br>• Program comparisons</div>
    </div>

    <div class="feat-card">
      <div class="feat-title">Why trust it?</div>
      <div>Runs fully in your browser — no Omnivox credentials, formula transparent.</div>
    </div>
  </div>

  <div class="footer-mini">
    RScore Pro © 2025 • Not affiliated with John Abbott College or Omnivox.
  </div>
</div>
""", unsafe_allow_html=True)

    # Embed buttons under their corresponding cards
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➡️ Continue with free tools"):
            st.session_state.onboarded = True
            st.rerun()
    with col2:
        if st.button("🚀 Unlock Pro (mock)"):
            st.session_state.is_premium = True
            st.session_state.onboarded = True
            st.rerun()


if not st.session_state.onboarded:
    show_landing()
    st.stop()
