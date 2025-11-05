import streamlit as st

# page config must be at the top
st.set_page_config(page_title="RScore Landing", layout="centered")

def show_landing():
    # you can put your fancy HTML back later — this is the safe version
    st.markdown("## RScore Pro")
    st.write(
        "Import Omnivox screenshots, autofill credits, compare programs. "
        "Manual entry stays free."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link("pages/Free.py", label="Free tools", icon="🟢")
    with col2:
        st.page_link("pages/Main.py", label="Pro (login)", icon="⭐")
    with col3:
        st.write("Runs in your browser.")

    st.markdown(
        "<p style='color:#999;font-size:12px;'>RScore Pro 2025 - not affiliated with JAC or Omnivox.</p>",
        unsafe_allow_html=True,
    )

def show_checkout():
    st.title("Upgrade to RScore Pro")
    st.write("You are signed in, but this account is not premium yet.")

    checkout_url = st.secrets.get("STRIPE_CHECKOUT_URL")
    if checkout_url:
        st.link_button("Pay with Stripe", checkout_url)
    else:
        st.warning("Add STRIPE_CHECKOUT_URL to Streamlit secrets to enable payment.")

# ---------- decide what to render ----------
# support both new and old Streamlit
try:
    qp = st.query_params  # newer
except AttributeError:
    qp = st.experimental_get_query_params()  # older

if "checkout" in qp:
    show_checkout()
else:
    show_landing()
