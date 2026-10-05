from datetime import date
from unittest.mock import Mock

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from components import mobile_recurrences as component
from utils.recorrencia import (
    STATUS_RECORRENCIA_ATIVA,
    STATUS_RECORRENCIA_CANCELADA,
    STATUS_RECORRENCIA_PAUSADA,
)


def _recorrencia(**alteracoes):
    registro = {
        "id": 1,
        "descricao": "Internet",
        "valor": 100.0,
        "tipo": "Despesa",
        "categoria": "Utilidades",
        "forma_pagamento": "PIX",
        "vencimento": 10,
        "periodicidade": "Mensal",
        "dia_programado": 10,
        "data_inicio": "2026-10-01",
        "data_fim": None,
        "status_recorrencia": STATUS_RECORRENCIA_ATIVA,
    }
    registro.update(alteracoes)
    return registro


def _app_formulario():
    def render_formulario():
        from components import mobile_recurrences

        mobile_recurrences.render_mobile_recurrence_form()

    return AppTest.from_function(render_formulario)


def test_formulario_abre_e_fecha():
    app = _app_formulario().run()

    assert app.button("recurrence_toggle_form").label == "🔄 Nova Recorrência"

    app.button("recurrence_toggle_form").click().run()
    assert app.button[1].label == "💾 Criar"
    assert app.button[2].label == "Cancelar"

    app.button[2].click().run()
    assert not app.session_state["recurrence_form_open"]


def test_criacao_valida_chama_service_e_nao_materializa(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        component.recurrence_service,
        "criar_recorrencia",
        lambda dados: chamadas.append(dados),
    )
    monkeypatch.setattr(
        component.recurrence_service,
        "materializar_recorrencia",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("materialização não deveria ser chamada")
        ),
    )
    monkeypatch.setattr(
        component.recurrence_service,
        "sincronizar_recorrencias",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("sincronização não deveria ser chamada")
        ),
    )

    app = _app_formulario().run()
    app.button("recurrence_toggle_form").click().run()
    app.text_input[0].set_value("Internet").run()
    app.number_input[0].set_value(100.0).run()
    app.button[1].click().run()

    assert chamadas == [
        {
            "descricao": "Internet",
            "valor": 100.0,
            "tipo": "Receita",
            "categoria": "Moradia",
            "forma_pagamento": "PIX",
            "vencimento": None,
            "periodicidade": "Mensal",
            "dia_programado": 1,
            "data_inicio": date.today(),
            "data_fim": None,
        }
    ]


def test_criacao_com_valor_none_envia_none(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        component.recurrence_service,
        "criar_recorrencia",
        lambda dados: chamadas.append(dados),
    )

    app = _app_formulario().run()
    app.button("recurrence_toggle_form").click().run()
    app.text_input[0].set_value("Internet").run()
    app.checkbox[0].check().run()
    app.button[1].click().run()

    assert chamadas[0]["valor"] is None


def test_criacao_invalida_exibe_erro_visual(monkeypatch):
    criar = Mock()
    monkeypatch.setattr(component.recurrence_service, "criar_recorrencia", criar)

    app = _app_formulario().run()
    app.button("recurrence_toggle_form").click().run()
    app.button[1].click().run()

    assert app.error[0].value == "Informe uma descrição."
    assert criar.call_count == 0


@pytest.mark.parametrize("mensagem", ["Categoria inválida.", "Forma inválida."])
def test_service_value_error_e_exibido(monkeypatch, mensagem):
    monkeypatch.setattr(
        component.recurrence_service,
        "criar_recorrencia",
        lambda _dados: (_ for _ in ()).throw(ValueError(mensagem)),
    )

    app = _app_formulario().run()
    app.button("recurrence_toggle_form").click().run()
    app.text_input[0].set_value("Internet").run()
    app.number_input[0].set_value(100.0).run()
    app.button[1].click().run()

    assert app.error[0].value == mensagem


def test_data_inicial_e_final_sao_enviadas(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        component.recurrence_service,
        "criar_recorrencia",
        lambda dados: chamadas.append(dados),
    )

    app = _app_formulario().run()
    app.button("recurrence_toggle_form").click().run()
    app.text_input[0].set_value("Internet").run()
    app.number_input[0].set_value(100.0).run()
    app.checkbox[2].uncheck().run()
    app.button[1].click().run()

    assert chamadas[0]["data_inicio"] == date.today()
    assert chamadas[0]["data_fim"] == date.today()


def test_possui_vencimento_envia_dia(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        component.recurrence_service,
        "criar_recorrencia",
        lambda dados: chamadas.append(dados),
    )

    app = _app_formulario().run()
    app.button("recurrence_toggle_form").click().run()
    app.text_input[0].set_value("Internet").run()
    app.number_input[0].set_value(100.0).run()
    app.checkbox[1].check().run()
    app.number_input[1].set_value(15).run()
    app.button[1].click().run()

    assert chamadas[0]["vencimento"] == 15


def test_sem_vencimento_envia_none(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        component.recurrence_service,
        "criar_recorrencia",
        lambda dados: chamadas.append(dados),
    )

    app = _app_formulario().run()
    app.button("recurrence_toggle_form").click().run()
    app.text_input[0].set_value("Internet").run()
    app.number_input[0].set_value(100.0).run()
    app.button[1].click().run()

    assert chamadas[0]["vencimento"] is None


def test_filtro_por_status():
    registros = [
        _recorrencia(status_recorrencia=STATUS_RECORRENCIA_ATIVA),
        _recorrencia(id=2, status_recorrencia=STATUS_RECORRENCIA_PAUSADA),
    ]

    resultado = component._filtrar_recorrencias(registros, "Pausadas")

    assert resultado == [registros[1]]


def test_busca_por_descricao_e_categoria():
    registros = [
        _recorrencia(descricao="Internet"),
        _recorrencia(id=2, descricao="Aluguel", categoria="Moradia"),
    ]

    assert component._filtrar_recorrencias(registros, busca="internet") == [
        registros[0]
    ]
    assert component._filtrar_recorrencias(registros, busca="moradia") == [
        registros[1]
    ]


def test_ordenacao_prioriza_status_e_depois_dia():
    registros = [
        _recorrencia(
            id=1,
            status_recorrencia=STATUS_RECORRENCIA_CANCELADA,
            dia_programado=1,
        ),
        _recorrencia(
            id=2,
            status_recorrencia=STATUS_RECORRENCIA_ATIVA,
            dia_programado=20,
        ),
        _recorrencia(
            id=3,
            status_recorrencia=STATUS_RECORRENCIA_ATIVA,
            dia_programado=10,
        ),
        _recorrencia(
            id=4,
            status_recorrencia=STATUS_RECORRENCIA_PAUSADA,
            dia_programado=5,
        ),
    ]

    ordenadas = component._ordenar_recorrencias(registros)

    assert [registro["id"] for registro in ordenadas] == [3, 2, 4, 1]


def test_formatacao_de_dia_exibe_inteiro():
    assert component._formatar_dia_exibicao(10) == "10"
    assert component._formatar_dia_exibicao(10.0) == "10"


def test_formatacao_de_vencimento_exibe_sem_nan():
    assert component._formatar_vencimento_exibicao(10) == "dia 10"
    assert component._formatar_vencimento_exibicao(10.0) == "dia 10"
    assert component._formatar_vencimento_exibicao(None) == "sem vencimento"
    assert component._formatar_vencimento_exibicao(float("nan")) == "sem vencimento"


def test_listagem_usa_service_e_exibe_valor_nao_informado(monkeypatch):
    exibicoes = []
    monkeypatch.setattr(
        component.recurrence_service,
        "listar_recorrencias",
        lambda: pd.DataFrame([_recorrencia(valor=None)]),
    )
    monkeypatch.setattr(
        component.st,
        "markdown",
        lambda texto, **_kwargs: exibicoes.append(texto),
    )
    monkeypatch.setattr(component.st, "caption", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(component.st, "info", lambda *_args, **_kwargs: None)

    component.render_mobile_recurrence_list()

    assert any("Valor não informado" in texto for texto in exibicoes)


def test_card_nao_exibe_nan_nem_decimal_no_dia(monkeypatch):
    captions = []
    monkeypatch.setattr(component.st, "markdown", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        component.st,
        "caption",
        lambda texto, **_kwargs: captions.append(texto),
    )

    component._render_recorrencia_card(
        _recorrencia(
            dia_programado=10.0,
            vencimento=None,
        )
    )

    assert any("Dia 10" in texto for texto in captions)
    assert any("Vencimento: sem vencimento" in texto for texto in captions)
    assert all("10.0" not in texto and "nan" not in texto.casefold() for texto in captions)
