from datetime import date
from unittest.mock import Mock

from streamlit.testing.v1 import AppTest

from components import mobile_transactions
from utils.status import STATUS_PAGO


def _app_formulario():
    def render():
        from components.mobile_transactions import render_mobile_transaction_form

        render_mobile_transaction_form(2026, "OUTUBRO")

    return AppTest.from_function(render)


def test_criacao_mobile_paga_envia_data_efetiva_ao_servico(monkeypatch):
    inserir = Mock()
    monkeypatch.setattr(mobile_transactions, "inserir_parcelado", inserir)

    app = _app_formulario().run()
    app.button[0].click().run()
    app.text_input[0].set_value("Academia").run()
    app.number_input[0].set_value(100.0).run()
    next(item for item in app.selectbox if item.label == "Categoria").set_value("Moradia").run()
    next(item for item in app.selectbox if item.label == "Status").set_value(STATUS_PAGO).run()

    assert any(item.label == "Data efetiva do pagamento" for item in app.date_input)
    next(item for item in app.button if item.label == "💾 Salvar transação").click().run()

    assert inserir.call_args.kwargs["status"] == STATUS_PAGO
    assert inserir.call_args.kwargs["data_liquidacao"] == date.today()


def test_criacao_mobile_pendente_nao_envia_data_de_liquidacao(monkeypatch):
    inserir = Mock()
    monkeypatch.setattr(mobile_transactions, "inserir_parcelado", inserir)

    app = _app_formulario().run()
    app.button[0].click().run()
    app.text_input[0].set_value("Academia").run()
    app.number_input[0].set_value(100.0).run()
    next(item for item in app.selectbox if item.label == "Categoria").set_value("Moradia").run()
    next(item for item in app.button if item.label == "💾 Salvar transação").click().run()

    assert inserir.call_args.kwargs["data_liquidacao"] is None
