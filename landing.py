import streamlit as st

st.set_page_config(page_title="RScore Landing", page_icon="📊", layout="centered")

def show_landing():
    st.markdown(
        """
        <style>
        body {
            background-color: #f9fafb;
            margin: 0;
            padding: 0;
            overflow-x: hidden; /* ✅ removes side scroll globally */
        }

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
            border-radius: 9999px;
            font-size: .7rem;
        }

        /* 3 boxes centered perfectly without scrolling */
        .features {
            display: flex;
            justify-content: center;
            align-items: stretch;
            gap: 1.5rem;
            margin-top: 2.5rem;
            flex-wrap: wrap; /* ✅ allows neat wrapping instead of scroll */
        }

        .feat-card {
            text-decoration: none !important;
            color: inherit !important;
            background: #ffffff;
            border: 2px solid #e5e7eb;
            border-radius: 1rem;
            padding: 1.5rem 1.5rem 1.2rem 1.5rem;
            width: 260px;
            min-height: 180px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            transition: all .15s ease-in-out;
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }

        .feat-card:hover {
            transform: scale(1.03);
            border-color: #6366F1;
            box-shadow: 0 10px 25px rgba(99,102,241,0.15);
        }

        .feat-title {
            font-weight: 700;
            font-size: 1.05rem;
            margin-bottom: .45rem;
        }

        .feat-card p {
            font-size: .9rem;
            line-height: 1.35;
            margin: 0;
        }

        /* PRO card stands out */
        .pro-card {
            background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
            border: none;
            color: #ffffff !important;
            box-shadow: 0 10px 25px rgba(99,102,241,0.25);
        }

        .pro-card .feat-title,
        .pro-card p {
            color: #ffffff !important;
        }

        .pro-card:hover {
            transform: scale(1.05);
            box-shadow: 0 15px 35px rgba(79,70,229,0.4);
        }

        .footer-mini {
            margin-top: 2.5rem;
            text-align: center;
            font-size: .75rem;
            color: #9ca3af;
        }
        </style>

    <div class="hero-wrap">
        <div style="display:flex;justify-content:center;margin-bottom:1rem;">
            <div style="background:rgba(99,102,241,.12);padding:.35rem .75rem;border-radius:9999px;font-size:.7rem;color:#4f46e5;">
                RScore Pro • Quebec CEGEP R-score helper
            </div>
        </div>

    <div class="hero-title">Your R-Score, cleaned up.</div>
        <div class="hero-sub">
            Import Omnivox screenshots, autofill credits, see admission ranges, and track scenarios.<br>
            Manual entry stays free.
        </div>
    <div class="hero-badges">
            <div class="hero-badge">✓ No Omnivox password stored</div>
            <div class="hero-badge">✓ Uses standard 35 + 5 × Z</div>
            <div class="hero-badge">✓ Built for JAC students</div>
        </div>

    <div class="features">
            <a href="/Main" target="_self" class="feat-card">
    <div class="feat-title">Free Tools</div>
                <p>Manual entry<br>R-score calculation<br>Min/max settings</p>
            </a>
            <a href="/Main" target="_self" class="feat-card pro-card">
    <div class="feat-title">Pro</div>
                <p>OCR import<br>Autofill credits<br>Program comparisons</p>
            </a>
    <div class="feat-card" style="cursor:default;">
    <div class="feat-title">Why trust it?</div>
                <p>Runs fully in your browser<br>No Omnivox credentials<br>Formula shown</p>
    </div>
    </div>
    <div class="footer-mini">
            RScore Pro © 2025 • Not affiliated with John Abbott College or Omnivox.
        </div>
    </div>
    """, unsafe_allow_html=True)

show_landing()
