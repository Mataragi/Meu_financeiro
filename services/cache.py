import streamlit as st


cache_data = st.cache_data


def invalidar_cache(funcao_cacheada):
    """Invalida somente os resultados da função decorada informada."""
    funcao_cacheada.clear()
