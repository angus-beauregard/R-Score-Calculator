import streamlit as st

st.set_page_config(page_title="RScore Landing", layout="centered")

def show_landing():
    st.markdown("## RScore Pro")
    st.write(
        "Import Omnivox screenshots, autofill credits, compare programs. "
        "Manual entry stays free."
    )
    # links to your other pages
    st.page_link("pages/Free.py", label="Free tools", icon="🟢")
    st.page_link("pages/Main.py", label="Pro (login)", icon="⭐")
    st.markdown(
        "<p style='color:#999;font-size:12px;'>RScore Pro 2025 - not affiliated with JAC or Omnivox.</p>",
        unsafe_allow_html=True,
    )

def show_checkout():
    st.title("Upgrade to RScore Pro")
    st.write("You're signed in but this account is not premium yet.")
    checkout_url = st.secrets.get("STRIPE_CHECKOUT_URL")
    if checkout_url:
        st.link_button("Pay with Stripe", checkout_url)
    else:
        st.warning("Add STRIPE_CHECKOUT_URL to Streamlit secrets to enable payment.")

# ✅ ONLY use st.query_params
qp = st.query_params
if "checkout" in qp:
    show_checkout()
else:
    show_landing()
