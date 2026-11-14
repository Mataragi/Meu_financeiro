import os

import streamlit as st
from supabase import create_client


def _configuracao_supabase():
    ambiente = os.getenv("FINANCEIRO_PRO_ENV", "production").strip().lower()

    if ambiente == "demo":
        # Nunca reutiliza credenciais de produção como fallback.
        configuracao = st.secrets.get("demo", {})
        url = configuracao.get("SUPABASE_URL")
        chave = configuracao.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not chave:
            raise RuntimeError(
                "Ambiente demo selecionado, mas faltam [demo].SUPABASE_URL "
                "e [demo].SUPABASE_SERVICE_ROLE_KEY nos secrets do Streamlit. "
                "Configure um projeto Supabase exclusivo para demonstração."
            )
        return url, chave

    if ambiente != "production":
        raise RuntimeError(
            "FINANCEIRO_PRO_ENV inválido. Use 'production' ou 'demo'."
        )

    try:
        return (
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_SERVICE_ROLE_KEY"],
        )
    except KeyError as exc:
        raise RuntimeError(
            "Configure SUPABASE_SERVICE_ROLE_KEY somente nos secrets do "
            "servidor Streamlit. Chaves anon não são autorizadas para este app."
        ) from exc


@st.cache_resource
def init_supabase():
    url, chave = _configuracao_supabase()
    return create_client(url, chave)


class _ClienteSupabaseTardio:
    """Inicializa o cliente somente no primeiro acesso ao banco.

    Isso preserva o fail-closed da configuração de credenciais, mas permite
    importar serviços puros e substituir o repositório em testes sem acessar
    secrets nem criar uma conexão externa.
    """

    def __getattr__(self, atributo):
        return getattr(init_supabase(), atributo)


supabase = _ClienteSupabaseTardio()
