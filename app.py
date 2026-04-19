import streamlit as st
from components.sidebar import render_sidebar
from components.dashboard import render_dashboard

st.set_page_config(page_title="Financeiro Pro", layout="wide")
st.title("💰 Financeiro Pro")

render_sidebar()
render_dashboard()