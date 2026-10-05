from contextlib import nullcontext

import pandas as pd

from components import mobile
from components import mobile_actions, mobile_transactions
from components.mobile_helpers import valor_seguro
from utils.formatacao import formatar_valor_exibicao


def test_mobile_compose_recorrencias_uma_vez_na_ordem_aprovada(monkeypatch):
    eventos = []

    monkeypatch.setattr(mobile, "_render_select_style", lambda: None)
    monkeypatch.setattr(mobile, "_render_mobile_styles", lambda: None)
    monkeypatch.setattr(mobile, "_render_mobile_header", lambda: None)
    monkeypatch.setattr(
        mobile,
        "_render_filters",
        lambda: eventos.append("filtros") or (2026, "OUTUBRO", "Todos"),
    )
    monkeypatch.setattr(
        mobile.recurrence_service,
        "sincronizar_recorrencias",
        lambda ano, mes: eventos.append(("sincronizar", ano, mes)),
    )
    monkeypatch.setattr(
        mobile,
        "carregar_dados",
        lambda mes, ano: eventos.append(("carregar", mes, ano))
        or pd.DataFrame(),
    )
    monkeypatch.setattr(
        mobile,
        "_render_metrics",
        lambda _df: eventos.append("metricas"),
    )
    monkeypatch.setattr(
        mobile,
        "render_mobile_transaction_form",
        lambda ano, mes: eventos.append(("nova_transacao", ano, mes)),
    )
    monkeypatch.setattr(
        mobile,
        "render_mobile_recurrence_form",
        lambda: eventos.append("nova_recorrencia"),
    )
    monkeypatch.setattr(
        mobile,
        "render_mobile_transaction_list",
        lambda df, mes, status_view: eventos.append(
            ("transacoes", mes, status_view)
        ),
    )
    monkeypatch.setattr(
        mobile,
        "render_mobile_recurrence_list",
        lambda: eventos.append("recorrencias"),
    )
    monkeypatch.setattr(
        mobile,
        "render_mobile_transaction_actions",
        lambda df, mes: eventos.append(("acoes", mes)),
    )
    monkeypatch.setattr(
        mobile,
        "render_mobile_tools",
        lambda: eventos.append("ferramentas"),
    )
    monkeypatch.setattr(
        mobile,
        "render_mobile_debts",
        lambda: eventos.append("dividas"),
    )
    monkeypatch.setattr(mobile.st, "divider", lambda: None)
    monkeypatch.setattr(mobile.st, "markdown", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(mobile.st, "container", lambda **_kwargs: nullcontext())

    mobile.render_mobile()

    assert eventos == [
        "filtros",
        ("sincronizar", 2026, "OUTUBRO"),
        ("carregar", "OUTUBRO", 2026),
        "metricas",
        ("nova_transacao", 2026, "OUTUBRO"),
        "nova_recorrencia",
        ("transacoes", "OUTUBRO", "Todos"),
        "recorrencias",
        ("acoes", "OUTUBRO"),
        "ferramentas",
        "dividas",
    ]
    assert eventos.count("nova_recorrencia") == 1
    assert eventos.count("recorrencias") == 1
    assert sum(1 for evento in eventos if isinstance(evento, tuple) and evento[0] == "sincronizar") == 1


def test_abrir_mes_especifico_sincroniza_antes_de_carregar(monkeypatch):
    eventos = []

    def sincronizar(ano, mes):
        eventos.append(("sincronizar", ano, mes))

    def carregar(mes, ano):
        eventos.append(("carregar", mes, ano))
        return pd.DataFrame([{"descricao": "Internet", "mes": mes, "ano": ano}])

    monkeypatch.setattr(mobile.recurrence_service, "sincronizar_recorrencias", sincronizar)
    monkeypatch.setattr(mobile, "carregar_dados", carregar)

    dados = mobile._carregar_dados_da_competencia(2026, "OUTUBRO")

    assert eventos == [
        ("sincronizar", 2026, "OUTUBRO"),
        ("carregar", "OUTUBRO", 2026),
    ]
    assert dados.to_dict("records") == [
        {"descricao": "Internet", "mes": "OUTUBRO", "ano": 2026}
    ]


def test_trocar_mes_sincroniza_a_nova_competencia(monkeypatch):
    sincronizacoes = []
    carregamentos = []

    monkeypatch.setattr(
        mobile.recurrence_service,
        "sincronizar_recorrencias",
        lambda ano, mes: sincronizacoes.append((ano, mes)),
    )
    monkeypatch.setattr(
        mobile,
        "carregar_dados",
        lambda mes, ano: carregamentos.append((mes, ano)) or pd.DataFrame(),
    )

    mobile._carregar_dados_da_competencia(2026, "OUTUBRO")
    mobile._carregar_dados_da_competencia(2026, "NOVEMBRO")

    assert sincronizacoes == [(2026, "OUTUBRO"), (2026, "NOVEMBRO")]
    assert carregamentos == [("OUTUBRO", 2026), ("NOVEMBRO", 2026)]


def test_todos_nao_sincroniza_e_preserva_carregamento_existente(monkeypatch):
    sincronizacoes = []
    carregamentos = []

    monkeypatch.setattr(
        mobile.recurrence_service,
        "sincronizar_recorrencias",
        lambda ano, mes: sincronizacoes.append((ano, mes)),
    )
    monkeypatch.setattr(
        mobile,
        "carregar_dados",
        lambda mes, ano: carregamentos.append((mes, ano)) or pd.DataFrame(),
    )

    mobile._carregar_dados_da_competencia(2026, "TODOS")

    assert sincronizacoes == []
    assert carregamentos == [("TODOS", 2026)]


def test_selecione_nao_sincroniza_nem_carrega(monkeypatch):
    sincronizacoes = []
    carregamentos = []

    monkeypatch.setattr(
        mobile.recurrence_service,
        "sincronizar_recorrencias",
        lambda ano, mes: sincronizacoes.append((ano, mes)),
    )
    monkeypatch.setattr(
        mobile,
        "carregar_dados",
        lambda mes, ano: carregamentos.append((mes, ano)) or pd.DataFrame(),
    )

    dados = mobile._carregar_dados_da_competencia(2026, "Selecione")

    assert sincronizacoes == []
    assert carregamentos == []
    assert dados.empty


def test_ano_ou_mes_invalidos_nao_sincronizam(monkeypatch):
    sincronizacoes = []

    monkeypatch.setattr(mobile, "carregar_dados", lambda mes, ano: pd.DataFrame())
    monkeypatch.setattr(
        mobile.recurrence_service,
        "sincronizar_recorrencias",
        lambda ano, mes: sincronizacoes.append((ano, mes)),
    )

    mobile._carregar_dados_da_competencia(2099, "OUTUBRO")
    mobile._carregar_dados_da_competencia(2026, "MES_INVALIDO")

    assert sincronizacoes == []


def test_ocorrencia_materializada_aparece_no_carregamento(monkeypatch):
    ocorrencias = []

    def sincronizar(ano, mes):
        ocorrencias.append(
            {"descricao": "Internet", "mes": mes, "ano": ano}
        )

    monkeypatch.setattr(mobile.recurrence_service, "sincronizar_recorrencias", sincronizar)
    monkeypatch.setattr(
        mobile,
        "carregar_dados",
        lambda mes, ano: pd.DataFrame(
            registro for registro in ocorrencias
            if registro["mes"] == mes and registro["ano"] == ano
        ),
    )

    dados = mobile._carregar_dados_da_competencia(2026, "OUTUBRO")

    assert dados.to_dict("records") == [
        {"descricao": "Internet", "mes": "OUTUBRO", "ano": 2026}
    ]


def test_rerender_reutiliza_idempotencia_do_motor(monkeypatch):
    ocorrencias = set()
    sincronizacoes = []

    def sincronizar(ano, mes):
        sincronizacoes.append((ano, mes))
        ocorrencias.add((ano, mes))

    monkeypatch.setattr(mobile.recurrence_service, "sincronizar_recorrencias", sincronizar)
    monkeypatch.setattr(
        mobile,
        "carregar_dados",
        lambda mes, ano: pd.DataFrame(
            [{"mes": mes, "ano": ano}]
            if (ano, mes) in ocorrencias
            else []
        ),
    )

    primeira = mobile._carregar_dados_da_competencia(2026, "OUTUBRO")
    segunda = mobile._carregar_dados_da_competencia(2026, "OUTUBRO")

    assert len(sincronizacoes) == 2
    assert len(primeira) == 1
    assert len(segunda) == 1
    assert len(ocorrencias) == 1


def test_valor_nulo_e_zero_sao_distintos_na_apresentacao():
    assert formatar_valor_exibicao(None) == "Valor não informado"
    assert formatar_valor_exibicao(float("nan")) == "Valor não informado"
    assert formatar_valor_exibicao(0) == "R$ 0,00"
    assert valor_seguro(None) is None
    assert valor_seguro(0) == 0.0


def test_resumo_de_ocorrencia_nula_nao_executa_float_none(monkeypatch):
    exibicoes = []
    monkeypatch.setattr(
        mobile_transactions.st,
        "markdown",
        lambda conteudo, **_kwargs: exibicoes.append(conteudo),
    )

    mobile_transactions._render_transaction_summary(
        {
            "descricao": "Internet",
            "valor": None,
            "tipo": "Despesa",
            "status": "Pendente",
        }
    )

    assert "Valor não informado" in exibicoes[0]


def test_acoes_exibem_valor_nulo_sem_excecao():
    opcoes = mobile_actions._opcoes_registros(
        pd.DataFrame(
            [
                {
                    "id": 7,
                    "descricao": "Internet",
                    "valor": None,
                    "status": "Pendente",
                },
                {
                    "id": 8,
                    "descricao": "Taxa",
                    "valor": 0.0,
                    "status": "Pendente",
                },
            ]
        ),
        incluir_status=True,
    )

    assert any("Valor não informado" in label for label in opcoes)
    assert any("R$ 0,00" in label for label in opcoes)
