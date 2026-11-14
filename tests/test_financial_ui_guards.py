import pandas as pd
from streamlit.testing.v1 import AppTest

from components import mobile, mobile_transactions
from utils.status import STATUS_PAGO


def test_mobile_metrics_show_warning_when_reference_precedes_opening_balance(monkeypatch):
    def fail_reference(_reference):
        raise ValueError("A data de referência não pode ser anterior à data-base.")

    monkeypatch.setattr(mobile, "calcular_posicao_configurada", fail_reference)

    app = AppTest.from_string(
        """
import pandas as pd
import streamlit as st
from components import mobile
st.session_state.ano_mobile = 2026
st.session_state.mes_mobile = "JANEIRO"
mobile._render_metrics(pd.DataFrame())
"""
    ).run()

    assert not app.exception
    assert any(
        "Selecione uma competência igual ou posterior à data-base" in item.value
        for item in app.warning
    )


def test_paid_transaction_status_and_payment_method_are_locked(monkeypatch):
    monkeypatch.setattr(mobile_transactions, "atualizar_registro", lambda *_args: None)

    app = AppTest.from_string(
        """
from components import mobile_transactions
mobile_transactions._render_edicao_inline({
    "id": 9001,
    "descricao": "Conta já paga",
    "valor": 120.0,
    "categoria": "Moradia",
    "forma_pagamento": "PIX",
    "status": "Pago",
    "vencimento": 10,
    "data_transacao": "2026-10-10",
    "data_liquidacao": "2026-10-10",
})
"""
    ).run()

    assert not app.exception
    status = next(item for item in app.selectbox if item.label == "Status")
    forma = next(item for item in app.selectbox if item.label == "Forma de pagamento")
    assert status.disabled is True
    assert status.value == STATUS_PAGO
    assert forma.disabled is True
