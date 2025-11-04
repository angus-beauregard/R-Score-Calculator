import streamlit as st

st.set_page_config(page_title="RScore Landing", layout="centered")

# read query params
qp = st.query_params
mode = qp.get("mode", [""])[0] if isinstance(qp.get("mode"), list) else qp.get("mode", "")

# if we came here specifically to login, bounce to the premium app (workingv1.py)
# you can rename to whatever your premium file is called
if mode == "login":
    # this page just decides “you must log in”, so go to the app that contains the login
    st.switch_page("main.py")

st.markdown("""
    <style>
    .hero-wrap {max-width: 960px; margin: 0 auto; padding: 2.5rem 1.5rem 2rem 1.5rem; text-align: center;}
    .hero-title {font-size: clamp(2.3rem, 4vw, 2.8rem); font-weight: 700; color: #111827;}
    .hero-sub {margin-top: 1rem; font-size: 1rem; color: #4b5563;}
    .hero-badges {margin-top: 1.2rem; display:flex; gap:.6rem; justify-content:center; flex-wrap:wrap;}
    .hero-badge {background: rgba(79,70,229,0.08); border: 1px solid rgba(79,70,229,0.15); padding:.35rem .7rem; border-radius:9999px; font-size:.7rem;}

    .features {display:flex; justify-content:center; gap:1.2rem; margin-top:2.5rem; flex-wrap:wrap;}
    .feat-card {text-decoration:none !important; background:#fff; border:2px solid #e5e7eb; border-radius:1rem;
                padding:1.5rem 1.5rem 1.2rem 1.5rem; width:260px; min-height:180px;
                box-shadow:0 5px 15px rgba(0,0,0,0.05); transition:.15s; text-align:center;}
    .feat-card:hover {transform:scale(1.03); border-color:#6366F1;}
    .feat-title {font-weight:700; font-size:1.05rem; margin-bottom:.45rem;}
    .feat-card p {font-size:.9rem; line-height:1.35; margin:0;}
    .pro-card {background:linear-gradient(135deg, #4F46E5 0%, #6366F1 100%); border:none; color:#fff;}
    .pro-card .feat-title, .pro-card p {color:#fff;}
    .pro-card:hover {transform:scale(1.05);}

    .top-login {
    margin-top: 1.5rem;
    }
    .login-link {
    display:inline-block;
    background: #ffffff;
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 9999px;
    padding: .45rem 1.1rem;
    font-size: .85rem;
    color: #4F46E5;
    text-decoration:none !important;
    }
    .login-link:hover {
    background:#4F46E5;
    color:#fff;
    }
    .footer-mini {margin-top:2.5rem; text-align:center; font-size:.75rem; color:#9ca3af;}
    </style>
<div class="hero-wrap">
    <div style="background:rgba(99,102,241,.12);padding:.35rem .75rem;border-radius:9999px;font-size:.7rem;color:#4f46e5;display:inline-block;">
        RScore Pro • Quebec CEGEP R-score helper
    </div>
    <div class="hero-title">Your R-Score, cleaned up.</div>
    <div class="hero-sub">Manual stays free. OCR, CSV and extras are premium.</div>

<div class="hero-badges">
    <div class="hero-badge">✓ No Omnivox password stored</div>
    <div class="hero-badge">✓ Uses standard 35 + 5 × Z</div>        
    <div class="hero-badge">✓ Built for JAC students</div>
</div>

<div class="top-login">
    <!-- goes to this same page with ?mode=login which then switch_page(...) above -->
    <a href="?mode=login" class="login-link">Sign in / Create account</a>
</div>

<div class="features">
    <!-- FREE: go straight to free version -->
    <a href="/free" target="_self" class="feat-card">
<div class="feat-title">Free tools</div>
    <p>Manual entry<br>R-score calculation<br>Basic settings</p>
    </a>
    <!-- PRO: force login/subscription -->
    <a href="?mode=login" class="feat-card pro-card">
<div class="feat-title">Pro (OCR, CSV)</div>
    <p>Upload screenshots<br>CSV import<br>Program comparisons</p>
    </a>
    <!-- INFO -->
<div class="feat-card" style="cursor:default;">
<div class="feat-title">Why trust it?</div>
    <p>Runs in browser<br>No Omnivox credentials<br>Formula shown</p>
</div>
</div>
<div class="footer-mini">
    RScoreCalc © 2025 • Not affiliated with John Abbott College or Omnivox.
</div>
</div>
""", unsafe_allow_html=True)
