"""Feedback seguro e uniforme para ações de liquidação nas interfaces."""

import logging

import requests
import streamlit as st

try:  # A classe concreta é fornecida pelo cliente PostgREST instalado.
    from postgrest.exceptions import APIError
except ImportError:  # pragma: no cover - mantém importável em ambientes mínimos
    APIError = ()


LOGGER = logging.getLogger(__name__)
ERROS_ESPERADOS_LIQUIDACAO = (ValueError, ConnectionError, TimeoutError, requests.RequestException)
if APIError:
    ERROS_ESPERADOS_LIQUIDACAO += (APIError,)


def executar_liquidacao(operacao, mensagem_sucesso):
    """Executa uma baixa e só anuncia sucesso após a confirmação do serviço.

    Falhas conhecidas não expõem a resposta bruta do banco. Exceções fora do
    contrato seguem sendo propagadas, para não mascarar regressões.
    """
    try:
        operacao()
    except ERROS_ESPERADOS_LIQUIDACAO as exc:
        LOGGER.warning("Falha esperada na liquidação: %s", type(exc).__name__)
        st.error(
            "Não foi possível concluir a liquidação. Verifique a data e o estado "
            "das transações e tente novamente."
        )
        return False
    st.success(mensagem_sucesso)
    return True
