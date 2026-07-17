import streamlit as st

from components.dashboard import render_dashboard
from components.mobile import render_mobile
from components.sidebar import render_sidebar

st.set_page_config(page_title="Financeiro Pro", layout="wide")

# Toggle mobile
is_mobile = st.toggle("📱 Modo Mobile", value=True)

st.title("💰 Financeiro Pro")

if is_mobile:
    render_mobile()
else:
    render_sidebar()
    render_dashboard()