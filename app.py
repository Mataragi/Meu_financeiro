import streamlit as st

from components.mobile import render_mobile

st.set_page_config(page_title="Financeiro Pro", layout="wide")
st.title("💰 Financeiro Pro")
render_mobile()
