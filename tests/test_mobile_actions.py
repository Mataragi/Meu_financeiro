from datetime import date
from unittest.mock import Mock

import pandas as pd
from streamlit.testing.v1 import AppTest

from components import mobile_actions


def _dados():
    return pd.DataFrame(
        [
            {
                "id": 101,
                "descricao": "Conta de luz",
                "valor": 120.0,
                "status": "Pendente",
                "forma_pagamento": "PIX",
                "tipo": "Despesa",
            },
            {
                "id": 202,
                "descricao": "Compra cartão",
                "valor": 350.0,
                "status": "Pendente",
                "forma_pagamento": "Crédito",
                "tipo": "Despesa",
            },
        ]
    )


def _app_baixa():
    def render(df):
        from components import mobile_actions

        mobile_actions._render_baixa(df, "OUTUBRO")

    return AppTest.from_function(render, args=[_dados()])


def test_baixa_mobile_envia_data_efetiva_para_lote(monkeypatch):
    liquidar = Mock()
    pagar_fatura = Mock()
    monkeypatch.setattr(mobile_actions, "dar_baixa_multiplos", liquidar)
    monkeypatch.setattr(mobile_actions, "liquidar_fatura_cartao", pagar_fatura)

    app = _app_baixa().run()
    assert app.date_input[0].label == "Data efetiva do pagamento"
    opcao = app.multiselect[0].options[0]
    app.multiselect[0].set_value([opcao]).run()
    app.button[0].click().run()

    liquidar.assert_called_once_with([101], date.today())
    pagar_fatura.assert_not_called()


def test_pagamento_fatura_credito_usa_servico_especifico(monkeypatch):
    liquidar = Mock()
    pagar_fatura = Mock()
    monkeypatch.setattr(mobile_actions, "dar_baixa_multiplos", liquidar)
    monkeypatch.setattr(mobile_actions, "liquidar_fatura_cartao", pagar_fatura)

    app = _app_baixa().run()
    assert any(metric.label == "Compras pendentes" and metric.value == "1" for metric in app.metric)
    assert any(metric.label == "Total da fatura" and "350" in metric.value for metric in app.metric)
    app.button[1].click().run()

    pagar_fatura.assert_called_once_with([202], date.today())
    liquidar.assert_not_called()


def test_fatura_nao_pode_ser_paga_com_compra_sem_valor(monkeypatch):
    pagar_fatura = Mock()
    monkeypatch.setattr(mobile_actions, "liquidar_fatura_cartao", pagar_fatura)
    dados = _dados()
    dados.loc[dados["id"] == 202, "valor"] = float("nan")

    def render(df):
        from components import mobile_actions

        mobile_actions._render_baixa(df, "OUTUBRO")

    app = AppTest.from_function(render, args=[dados]).run()

    assert any("sem valor informado" in item.value for item in app.warning)
    assert not any("Confirmar pagamento da fatura" in item.label for item in app.button)
    pagar_fatura.assert_not_called()


def test_falha_da_rpc_exibe_feedback_sem_anunciar_sucesso(monkeypatch):
    def falhar(*_args, **_kwargs):
        raise ValueError("estado concorrente")

    monkeypatch.setattr(mobile_actions, "dar_baixa_multiplos", falhar)

    app = _app_baixa().run()
    opcao = app.multiselect[0].options[0]
    app.multiselect[0].set_value([opcao]).run()
    app.button[0].click().run()

    assert any("Não foi possível concluir" in item.value for item in app.error)
    assert not any("liquidado(s)." in item.value for item in app.success)
