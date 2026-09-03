import streamlit as st


cache_data = st.cache_data


def invalidar_cache_consultas():
    st.cache_data.clear()
