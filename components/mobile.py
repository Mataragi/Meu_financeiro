import pandas as pd
import streamlit as st

from components.mobile_actions import render_mobile_transaction_actions
from components.mobile_constants import ANOS, MESES, STATUS_VIEW
from components.mobile_debts import render_mobile_debts
from components.mobile_helpers import calcular_metricas
from components.mobile_transactions import (
    render_mobile_transaction_form,
    render_mobile_transaction_list,
)
from services.database import carregar_dados
from utils.formatacao import formatar_real


def _render_select_style():
    st.markdown(
        """
        <style>
        div[data-baseweb="select"] input {
            caret-color: transparent;
            color: transparent !important;
            text-shadow: 0 0 0 white;
        }

        div[data-baseweb="select"] input:focus {
            outline: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_filters():
    ano = st.selectbox("Ano", ANOS, key="ano_mobile")
    mes = st.selectbox("📅 Mês", MESES, key="mes_mobile")
    status_view = st.selectbox("Status", STATUS_VIEW, key="status_view_mobile")
    return ano, mes, status_view


def _render_metrics(df_base):
    pagos, pendentes, saldo = calcular_metricas(df_base)
    coluna_pago, coluna_pendente, coluna_saldo = st.columns(3)
    coluna_pago.metric("Pago", formatar_real(pagos))
    coluna_pendente.metric("Pendente", formatar_real(pendentes))
    coluna_saldo.metric("Saldo", formatar_real(saldo))


def render_mobile():
    _render_select_style()
    ano, mes, status_view = _render_filters()
    df_base = pd.DataFrame() if mes == "Selecione" else carregar_dados(mes, ano)

    _render_metrics(df_base)
    st.divider()
    render_mobile_transaction_form(ano, mes)

    st.divider()
    render_mobile_transaction_list(df_base, mes, status_view)

    st.divider()
    render_mobile_transaction_actions(df_base, mes)

    st.divider()
    with st.expander("🤝 Dívidas informais"):
        render_mobile_debts()
