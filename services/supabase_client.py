import os

import streamlit as st
from supabase import create_client, Client


def _configuracao_supabase():
    ambiente = os.getenv("FINANCEIRO_PRO_ENV", "production").strip().lower()

    if ambiente == "demo":
        # Nunca reutiliza credenciais de produção como fallback.
        configuracao = st.secrets.get("demo", {})
        url = configuracao.get("SUPABASE_URL")
        chave = configuracao.get("SUPABASE_KEY")
        if not url or not chave:
            raise RuntimeError(
                "Ambiente demo selecionado, mas faltam [demo].SUPABASE_URL "
                "e [demo].SUPABASE_KEY nos secrets do Streamlit. "
                "Configure um projeto Supabase exclusivo para demonstração."
            )
        return url, chave

    if ambiente != "production":
        raise RuntimeError(
            "FINANCEIRO_PRO_ENV inválido. Use 'production' ou 'demo'."
        )

    return st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]


@st.cache_resource
def init_supabase():
    url, chave = _configuracao_supabase()
    return create_client(url, chave)


supabase: Client = init_supabase()