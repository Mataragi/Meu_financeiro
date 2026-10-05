from datetime import date

import pandas as pd
import streamlit as st

from components.mobile_actions import render_mobile_transaction_actions
from components.mobile_constants import ANOS, MESES, STATUS_VIEW
from components.mobile_debts import render_mobile_debts
from components.mobile_helpers import calcular_metricas
from components.mobile_recurrences import (
    render_mobile_recurrence_form,
    render_mobile_recurrence_list,
)
from components.mobile_tools import render_mobile_tools
from components.mobile_transactions import (
    render_mobile_transaction_form,
    render_mobile_transaction_list,
)
from services import recurrence_service
from services.transaction_service import MESES_ORDEM, carregar_dados
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

    st.components.v1.html(
        """
        <script>
        (() => {
            const parentDocument = window.parent.document;

            const bloquearTeclado = () => {
                parentDocument
                    .querySelectorAll('div[data-baseweb="select"] input')
                    .forEach((input) => {
                        input.setAttribute('readonly', 'readonly');
                        input.setAttribute('inputmode', 'none');
                        input.style.pointerEvents = 'none';

                        if (input.parentElement) {
                            input.parentElement.style.pointerEvents = 'auto';
                        }
                    });
            };

            bloquearTeclado();

            const observer = new MutationObserver(bloquearTeclado);
            observer.observe(parentDocument.body, {
                childList: true,
                subtree: true,
            });
        })();
        </script>
        """,
        height=0,
    )


def _render_mobile_header():
    st.markdown(
        """
        <div class="financeiro-pro-header">
            <div class="financeiro-pro-logo">💰</div>
            <div>
                <div class="financeiro-pro-eyebrow">CONTROLE FINANCEIRO</div>
                <div class="financeiro-pro-title">Financeiro Pro</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_mobile_styles():
    st.markdown(
        """
        <style>
        .financeiro-pro-header {
            align-items: center;
            background: linear-gradient(135deg, #12372a 0%, #1f6b4d 100%);
            border-radius: 20px;
            color: #f6fff9;
            display: flex;
            gap: 12px;
            margin: 0 0 18px;
            padding: 18px 20px;
        }

        .financeiro-pro-logo {
            align-items: center;
            background: rgba(255, 255, 255, 0.16);
            border-radius: 14px;
            display: flex;
            font-size: 25px;
            height: 48px;
            justify-content: center;
            width: 48px;
        }

        .financeiro-pro-eyebrow {
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            opacity: 0.72;
        }

        .financeiro-pro-title {
            font-size: 1.45rem;
            font-weight: 750;
            line-height: 1.15;
        }

        .financeiro-pro-metrics {
            display: grid;
            gap: 10px;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin: 4px 0 18px;
        }

        .financeiro-pro-card {
            background: #ffffff;
            border: 1px solid #e6ece8;
            border-radius: 16px;
            box-shadow: 0 4px 14px rgba(18, 55, 42, 0.06);
            min-width: 0;
            padding: 14px 12px;
        }

        .financeiro-pro-card-label {
            color: #66736d;
            font-size: 0.76rem;
            font-weight: 650;
            margin-bottom: 7px;
        }

        .financeiro-pro-card-value {
            color: #17382a;
            font-size: clamp(0.9rem, 3.7vw, 1.12rem);
            font-weight: 750;
            overflow-wrap: anywhere;
        }

        .financeiro-pro-transactions-title {
            color: #17382a;
            font-size: 1.2rem;
            font-weight: 750;
            margin: 8px 0 4px;
        }

        .financeiro-pro-transaction-search {
            margin-bottom: 12px;
        }

        .financeiro-pro-transaction-detail {
            align-items: flex-start;
            background: #fbfdfc;
            border: 1px solid #e6ece8;
            border-radius: 14px;
            display: flex;
            gap: 12px;
            margin: 8px 0 12px;
            padding: 12px;
        }

        .financeiro-pro-transaction-icon {
            align-items: center;
            background: #e8f3ed;
            border-radius: 12px;
            display: flex;
            flex: 0 0 40px;
            font-size: 20px;
            height: 40px;
            justify-content: center;
        }

        .financeiro-pro-transaction-main {
            flex: 1;
            min-width: 0;
        }

        .financeiro-pro-transaction-description {
            color: #17382a;
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.25;
            overflow-wrap: anywhere;
        }

        .financeiro-pro-transaction-meta {
            color: #66736d;
            font-size: 0.78rem;
            line-height: 1.35;
            margin-top: 4px;
        }

        .financeiro-pro-transaction-side {
            align-items: flex-end;
            display: flex;
            flex-direction: column;
            gap: 6px;
            text-align: right;
        }

        .financeiro-pro-status {
            border-radius: 999px;
            font-size: 0.68rem;
            font-weight: 700;
            padding: 4px 8px;
            white-space: nowrap;
        }

        .financeiro-pro-status-pago {
            background: #e2f4e9;
            color: #1d7446;
        }

        .financeiro-pro-status-pendente {
            background: #fff1d9;
            color: #996313;
        }

        .financeiro-pro-transaction-value {
            font-size: 0.95rem;
            font-weight: 750;
            white-space: nowrap;
        }

        .financeiro-pro-action-label,
        .financeiro-pro-actions-title {
            color: #66736d;
            font-size: 0.76rem;
            font-weight: 750;
            letter-spacing: 0.04em;
            margin: 10px 0 6px;
            text-transform: uppercase;
        }

        .financeiro-pro-value-receita {
            color: #1d7446;
        }

        .financeiro-pro-value-despesa {
            color: #b04a45;
        }

        @media (max-width: 640px) {
            .financeiro-pro-header {
                border-radius: 16px;
                padding: 15px 16px;
            }

            .financeiro-pro-title {
                font-size: 1.25rem;
            }

            .financeiro-pro-metrics {
                gap: 7px;
            }

            .financeiro-pro-card {
                border-radius: 13px;
                padding: 11px 9px;
            }

            .financeiro-pro-transaction-detail {
                gap: 9px;
                padding: 10px;
            }

            .financeiro-pro-transaction-side {
                gap: 4px;
            }

            .financeiro-pro-transaction-value {
                font-size: 0.84rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_filters():
    ano = st.selectbox("Ano", ANOS, key="ano_mobile")
    if "mes_mobile" not in st.session_state:
        mes_atual = MESES_ORDEM[date.today().month - 1]
        st.session_state.mes_mobile = mes_atual

    mes = st.selectbox(
        "📅 Mês",
        MESES,
        index=MESES.index(st.session_state.mes_mobile),
        key="mes_mobile",
    )
    status = st.selectbox(
        "Status",
        STATUS_VIEW,
        key="status_view_mobile",
    )
    return ano, mes, status


def _render_metrics(df_base):
    pagos, pendentes, saldo = calcular_metricas(df_base)
    cards = (
        ("Pago", formatar_real(pagos)),
        ("Pendente", formatar_real(pendentes)),
        ("Saldo calculado", formatar_real(saldo)),
    )
    cards_html = "".join(
        f'<div class="financeiro-pro-card">'
        f'<div class="financeiro-pro-card-label">{label}</div>'
        f'<div class="financeiro-pro-card-value">{value}</div>'
        "</div>"
        for label, value in cards
    )
    st.markdown(
        f'<div class="financeiro-pro-metrics">{cards_html}</div>',
        unsafe_allow_html=True,
    )


def _competencia_mobile_valida(ano, mes):
    return ano in ANOS and mes in MESES_ORDEM


def _carregar_dados_da_competencia(ano, mes):
    if _competencia_mobile_valida(ano, mes):
        recurrence_service.sincronizar_recorrencias(ano, mes)

    if mes == "Selecione" or mes not in MESES:
        return pd.DataFrame()

    return carregar_dados(mes, ano)


def render_mobile():
    _render_select_style()
    _render_mobile_styles()
    _render_mobile_header()
    ano, mes, status_view = _render_filters()
    df_base = _carregar_dados_da_competencia(ano, mes)

    _render_metrics(df_base)
    st.divider()
    render_mobile_transaction_form(ano, mes)
    render_mobile_recurrence_form()

    st.divider()
    render_mobile_transaction_list(df_base, mes, status_view=status_view)

    st.divider()
    render_mobile_recurrence_list()

    with st.container(border=True):
        st.markdown(
            '<div class="financeiro-pro-actions-title">Ações</div>',
            unsafe_allow_html=True,
        )
        render_mobile_transaction_actions(df_base, mes)
        render_mobile_tools()
        with st.expander("🤝 Dívidas informais"):
            render_mobile_debts()
