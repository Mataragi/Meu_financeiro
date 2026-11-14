from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pandas as pd
from streamlit.testing.v1 import AppTest

from components import mobile


def test_mobile_restores_monthly_metrics_when_opening_balance_is_missing(monkeypatch):
    monkeypatch.setattr(mobile, "carregar_saldo_inicial", lambda: None)

    app = AppTest.from_string(
        """
import pandas as pd
import streamlit as st
from components import mobile

st.session_state.ano_mobile = 2026
st.session_state.mes_mobile = "NOVEMBRO"
dados = pd.DataFrame([
    {"tipo": "Entrada", "status": "Pago", "valor": 1500.0},
    {"tipo": "Saída", "status": "Pago", "valor": 500.0},
    {"tipo": "Saída", "status": "Pendente", "valor": 200.0},
])
mobile._render_metrics(dados)
"""
    ).run()

    assert not app.exception
    markdown = "\n".join(item.value for item in app.markdown)
    assert "RESUMO DO MÊS" in markdown
    assert "Pago" in markdown
    assert "Pendente" in markdown
    assert "Saldo calculado" in markdown
    assert "R$ 500,00" in markdown
    assert "R$ 200,00" in markdown
    assert "R$ 1.000,00" in markdown
    assert "POSIÇÃO FINANCEIRA" in markdown
    assert "Saldo disponível" in markdown
    assert "Saldo projetado" in markdown
    assert any("A posição financeira depende" in item.value for item in app.info)


def test_mobile_shows_consolidated_indicators_when_opening_balance_exists(monkeypatch):
    abertura = SimpleNamespace(
        valor=Decimal("1000.00"),
        data_base=date(2026, 11, 1),
    )
    posicao = SimpleNamespace(
        saldo_disponivel=Decimal("1200.00"),
        resultado_acumulado=Decimal("800.00"),
        saldo_projetado=Decimal("900.00"),
    )
    monkeypatch.setattr(mobile, "carregar_saldo_inicial", lambda: abertura)
    monkeypatch.setattr(mobile, "calcular_posicao_configurada", lambda _ref: posicao)

    app = AppTest.from_string(
        """
import pandas as pd
import streamlit as st
from components import mobile

st.session_state.ano_mobile = 2026
st.session_state.mes_mobile = "NOVEMBRO"
mobile._render_metrics(pd.DataFrame([
    {"tipo": "Despesa", "status": "Pago", "valor": 100.0},
]))
"""
    ).run()

    assert not app.exception
    markdown = "\n".join(item.value for item in app.markdown)
    assert "RESUMO DO MÊS" in markdown
    assert "POSIÇÃO FINANCEIRA" in markdown
    assert "R$ 1.200,00" in markdown
    assert "R$ 800,00" in markdown
    assert "R$ 900,00" in markdown


def test_opening_balance_form_does_not_accept_empty_value_as_zero(monkeypatch):
    saved = []
    monkeypatch.setattr(
        mobile,
        "salvar_saldo_inicial",
        lambda valor, data_base: saved.append((valor, data_base)),
    )

    app = AppTest.from_string(
        """
from components import mobile
mobile._render_saldo_inicial_config(None)
"""
    ).run()

    assert not app.exception
    assert app.number_input[0].value is None

    app.button[0].click().run()

    assert not app.exception
    assert saved == []
    assert any("Informe o saldo real" in item.value for item in app.error)


def test_opening_balance_form_saves_explicit_value_and_base_date(monkeypatch):
    saved = []
    monkeypatch.setattr(
        mobile,
        "salvar_saldo_inicial",
        lambda valor, data_base: saved.append((valor, data_base)),
    )

    app = AppTest.from_string(
        """
from components import mobile
mobile._render_saldo_inicial_config(None)
"""
    ).run()

    app.number_input[0].set_value(1234.56)
    app.date_input[0].set_value(date(2026, 11, 13))
    app.button[0].click().run()

    assert not app.exception
    assert len(saved) == 1
    assert saved[0][0] == 1234.56
    assert saved[0][1] == date(2026, 11, 13)



def test_mobile_filters_expose_type_selector_with_all_as_default():
    app = AppTest.from_string(
        """
from components import mobile
mobile._render_filters()
"""
    ).run()

    assert not app.exception
    filtro = next(item for item in app.selectbox if item.label == "Tipo de transação")
    assert filtro.value == "Todos"
    assert filtro.options == ["Todos", "Receitas", "Despesas"]
