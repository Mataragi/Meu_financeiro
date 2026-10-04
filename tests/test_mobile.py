import pandas as pd

from components import mobile


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
