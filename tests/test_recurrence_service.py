from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

from services import database
from services import recurrence_service as service
from services import transaction_service
from utils.status import STATUS_PENDENTE


def _dados_recorrencia(**alteracoes):
    dados = {
        "descricao": "Internet",
        "valor": 100.0,
        "tipo": "Despesa",
        "categoria": "Utilidades",
        "forma_pagamento": "PIX",
        "vencimento": 10,
        "periodicidade": "Mensal",
        "dia_programado": 10,
        "data_inicio": "2026-10-10",
        "data_fim": None,
        "status_recorrencia": "Ativa",
    }
    dados.update(alteracoes)
    return dados


class FakeRecurrenceRepository:
    def __init__(self):
        self.registros = []
        self.atualizacoes = []

    def inserir_recorrencia(self, dados):
        registro = {"id": len(self.registros) + 1, **dados}
        self.registros.append(registro)
        return registro

    def carregar_recorrencias(self):
        return pd.DataFrame(self.registros)

    def carregar_recorrencia(self, id_recorrencia):
        return next(
            (registro for registro in self.registros if registro["id"] == id_recorrencia),
            None,
        )

    def atualizar_recorrencia(self, id_recorrencia, dados):
        registro = self.carregar_recorrencia(id_recorrencia)
        registro.update(dados)
        self.atualizacoes.append((id_recorrencia, dados))
        return registro


@pytest.fixture
def recurrence_repository(monkeypatch):
    repository = FakeRecurrenceRepository()
    monkeypatch.setattr(service, "database", repository)
    monkeypatch.setattr(service, "invalidar_cache_consultas", lambda: None)
    return repository


def test_criacao_de_recorrencia_valida(recurrence_repository):
    criada = service.criar_recorrencia(_dados_recorrencia())

    assert criada["id"] == 1
    assert criada["periodicidade"] == "Mensal"
    assert criada["dia_programado"] == 10
    assert criada["data_inicio"] == "2026-10-10"
    assert criada["status_recorrencia"] == "Ativa"


@pytest.mark.parametrize("tipo", ["Receita", "Despesa"])
def test_recorrencia_aceita_tipos_oficiais(recurrence_repository, tipo):
    criada = service.criar_recorrencia(_dados_recorrencia(tipo=tipo))

    assert criada["tipo"] == tipo


def test_recorrencia_aceita_valor_ausente_sem_transformar_em_zero():
    normalizada = service.normalizar_dados_recorrencia(
        _dados_recorrencia(valor=None)
    )

    assert normalizada["valor"] is None


def test_recorrencia_mensal_e_data_final_inclusiva():
    recorrencia = service.normalizar_dados_recorrencia(
        _dados_recorrencia(data_fim="2026-12-10")
    )

    assert service.elegivel_para_competencia(recorrencia, "2026-10") is True
    assert service.elegivel_para_competencia(recorrencia, "2026-12") is True
    assert service.elegivel_para_competencia(recorrencia, "2027-01") is False


def test_data_inicio_e_obrigatoria():
    dados = _dados_recorrencia()
    del dados["data_inicio"]

    with pytest.raises(ValueError, match="data_inicio"):
        service.normalizar_dados_recorrencia(dados)


def test_data_fim_nao_pode_ser_anterior_ao_inicio():
    with pytest.raises(ValueError, match="data_fim"):
        service.normalizar_dados_recorrencia(
            _dados_recorrencia(data_fim="2026-10-09")
        )


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("tipo", "Transferência"),
        ("forma_pagamento", "Cartão desconhecido"),
        ("categoria", "Categoria inexistente"),
        ("periodicidade", "Semanal"),
        ("dia_programado", 0),
        ("vencimento", 32),
        ("valor", 0),
    ],
)
def test_rejeita_campos_invalidos(campo, valor):
    with pytest.raises(ValueError):
        service.normalizar_dados_recorrencia(_dados_recorrencia(**{campo: valor}))


@pytest.mark.parametrize("status", ["Ativa", "Pausada", "Cancelada"])
def test_aceita_estados_do_lifecycle(recurrence_repository, status):
    criada = service.criar_recorrencia(
        _dados_recorrencia(status_recorrencia=status)
    )

    assert criada["status_recorrencia"] == status


def test_recorrencia_pausada_pode_ser_reativada(recurrence_repository):
    criada = service.criar_recorrencia(
        _dados_recorrencia(status_recorrencia="Pausada")
    )

    reativada = service.reativar_recorrencia(criada["id"])

    assert reativada["status_recorrencia"] == "Ativa"


def test_recorrencia_cancelada_nao_volta_para_ativa(recurrence_repository):
    criada = service.criar_recorrencia(_dados_recorrencia())
    service.cancelar_recorrencia(criada["id"])

    with pytest.raises(ValueError, match="cancelada"):
        service.reativar_recorrencia(criada["id"])


def test_recorrencia_pausada_nao_elegivel_e_cancelada_nao_elegivel():
    pausada = service.normalizar_dados_recorrencia(
        _dados_recorrencia(status_recorrencia="Pausada")
    )
    cancelada = service.normalizar_dados_recorrencia(
        _dados_recorrencia(status_recorrencia="Cancelada")
    )

    assert service.elegivel_para_competencia(pausada, "2026-10") is False
    assert service.elegivel_para_competencia(cancelada, "2026-10") is False


def test_chave_logica_da_ocorrencia_normaliza_mes():
    assert service.chave_ocorrencia(42, "2026-10") == (
        42,
        date(2026, 10, 1),
    )


def test_transacao_manual_nao_recebe_metadados_de_recorrencia():
    normalizada = transaction_service.normalizar_dados_transacao(
        {
            "descricao": "Compra manual",
            "tipo": "Despesa",
            "status": STATUS_PENDENTE,
        }
    )

    assert "recorrencia_id" not in normalizada
    assert "competencia_ocorrencia" not in normalizada


def test_persistencia_de_ocorrencia_ignora_conflito(monkeypatch):
    registros = []

    def inserir_transacao_recorrencia(dados):
        chave = (dados["recorrencia_id"], dados["competencia_ocorrencia"])
        if any(
            (registro["recorrencia_id"], registro["competencia_ocorrencia"]) == chave
            for registro in registros
        ):
            return SimpleNamespace(data=[])
        registros.append(dados)
        return SimpleNamespace(data=[dados])

    repository = SimpleNamespace(
        inserir_transacao_recorrencia=inserir_transacao_recorrencia
    )
    monkeypatch.setattr(transaction_service, "database", repository)
    monkeypatch.setattr(transaction_service, "invalidar_cache_consultas", lambda: None)

    dados = {
        "recorrencia_id": 42,
        "competencia_ocorrencia": date(2026, 10, 1),
        "ano": 2026,
        "mes": "OUTUBRO",
        "descricao": "Internet",
        "valor": 100.0,
        "tipo": "Despesa",
        "status": STATUS_PENDENTE,
        "categoria": "Utilidades",
        "forma_pagamento": "PIX",
        "data_transacao": date(2026, 10, 10),
    }

    transaction_service.inserir_ocorrencia_recorrencia(dados)
    transaction_service.inserir_ocorrencia_recorrencia(dados)

    assert len(registros) == 1


def test_repository_configura_upsert_atomico_para_chave_da_ocorrencia(monkeypatch):
    chamadas = {}

    class FakeQuery:
        def upsert(self, dados, **opcoes):
            chamadas["dados"] = dados
            chamadas["opcoes"] = opcoes
            return self

        def execute(self):
            return SimpleNamespace(data=[])

    class FakeSupabase:
        def table(self, nome):
            chamadas["tabela"] = nome
            return FakeQuery()

    monkeypatch.setattr(database, "supabase", FakeSupabase())

    database.inserir_transacao_recorrencia(
        {"recorrencia_id": 42, "competencia_ocorrencia": "2026-10-01"}
    )

    assert chamadas == {
        "tabela": "transacoes",
        "dados": {"recorrencia_id": 42, "competencia_ocorrencia": "2026-10-01"},
        "opcoes": {
            "on_conflict": "recorrencia_id,competencia_ocorrencia",
            "ignore_duplicates": True,
        },
    }


def _recorrencia_persistida(**alteracoes):
    return {"id": 42, **_dados_recorrencia(**alteracoes)}


def _capturar_materializacao(monkeypatch, resposta=None):
    payloads = []

    def inserir(dados):
        payloads.append(dados)
        return resposta or SimpleNamespace(data=[dados])

    monkeypatch.setattr(transaction_service, "inserir_ocorrencia_recorrencia", inserir)
    return payloads


@pytest.mark.parametrize(
    ("ano", "mes", "dia", "data_esperada"),
    [
        (2026, "FEVEREIRO", 28, date(2026, 2, 28)),
        (2028, "FEVEREIRO", 29, date(2028, 2, 29)),
        (2027, "FEVEREIRO", 29, date(2027, 2, 28)),
        (2026, "FEVEREIRO", 30, date(2026, 2, 28)),
        (2026, "ABRIL", 31, date(2026, 4, 30)),
        (2026, "DEZEMBRO", 31, date(2026, 12, 31)),
    ],
)
def test_materializacao_calcula_data_programada_deterministica(
    monkeypatch, ano, mes, dia, data_esperada
):
    payloads = _capturar_materializacao(monkeypatch)

    resultado = service.materializar_recorrencia(
        _recorrencia_persistida(dia_programado=dia, data_inicio="2026-01-01"),
        ano,
        mes,
    )

    assert resultado["criada"] is True
    assert payloads[0]["data_transacao"] == data_esperada


@pytest.mark.parametrize(
    ("status", "ano", "mes"),
    [
        ("Pausada", 2026, "OUTUBRO"),
        ("Cancelada", 2026, "OUTUBRO"),
        ("Ativa", 2026, "SETEMBRO"),
        ("Ativa", 2026, "NOVEMBRO"),
    ],
)
def test_materializacao_ignora_recorrencia_nao_elegivel(
    monkeypatch, status, ano, mes
):
    payloads = _capturar_materializacao(monkeypatch)
    dados = {"status_recorrencia": status}
    if mes == "SETEMBRO":
        dados["data_inicio"] = "2026-10-10"
    if mes == "NOVEMBRO":
        dados["data_fim"] = "2026-10-10"

    resultado = service.materializar_recorrencia(
        _recorrencia_persistida(**dados), ano, mes
    )

    assert resultado["elegivel"] is False
    assert resultado["materializada"] is False
    assert payloads == []


@pytest.mark.parametrize(
    ("tipo", "forma_pagamento"),
    [
        ("Receita", "PIX"),
        ("Despesa", "Débito"),
        ("Despesa", "Crédito"),
    ],
)
def test_materializacao_monta_payload_pendente(monkeypatch, tipo, forma_pagamento):
    payloads = _capturar_materializacao(monkeypatch)

    resultado = service.materializar_recorrencia(
        _recorrencia_persistida(
            tipo=tipo,
            forma_pagamento=forma_pagamento,
            valor=125.5,
            vencimento=15,
        ),
        2026,
        "OUTUBRO",
    )

    payload = payloads[0]
    assert resultado["criada"] is True
    assert payload["recorrencia_id"] == 42
    assert payload["competencia_ocorrencia"] == date(2026, 10, 1)
    assert payload["descricao"] == "Internet"
    assert payload["valor"] == 125.5
    assert payload["tipo"] == tipo
    assert payload["status"] == STATUS_PENDENTE
    assert payload["categoria"] == "Utilidades"
    assert payload["forma_pagamento"] == forma_pagamento
    assert payload["data_transacao"] == date(2026, 10, 10)
    assert payload["vencimento"] == 15
    assert payload["mes"] == "NOVEMBRO" if forma_pagamento == "Crédito" else "OUTUBRO"
    assert payload["ano"] == 2026


def test_materializacao_preserva_valor_desconhecido(monkeypatch):
    payloads = _capturar_materializacao(monkeypatch)

    service.materializar_recorrencia(
        _recorrencia_persistida(valor=None), 2026, "OUTUBRO"
    )

    assert payloads[0]["valor"] is None
    assert payloads[0]["status"] == STATUS_PENDENTE


@pytest.mark.parametrize(
    ("dia", "mes", "ano", "mes_esperado", "ano_esperado"),
    [
        (1, "OUTUBRO", 2026, "OUTUBRO", 2026),
        (4, "OUTUBRO", 2026, "OUTUBRO", 2026),
        (5, "OUTUBRO", 2026, "NOVEMBRO", 2026),
        (5, "DEZEMBRO", 2026, "JANEIRO", 2027),
    ],
)
def test_materializacao_reutiliza_competencia_de_credito(
    monkeypatch, dia, mes, ano, mes_esperado, ano_esperado
):
    payloads = _capturar_materializacao(monkeypatch)

    service.materializar_recorrencia(
        _recorrencia_persistida(
            dia_programado=dia,
            forma_pagamento="Crédito",
            data_inicio="2026-01-01",
        ),
        ano,
        mes,
    )

    assert payloads[0]["mes"] == mes_esperado
    assert payloads[0]["ano"] == ano_esperado
    assert payloads[0]["competencia_ocorrencia"] == date(ano, 10 if mes == "OUTUBRO" else 12, 1)


def test_materializacao_repetida_e_idempotente(monkeypatch):
    registros = {}

    def inserir(dados):
        chave = (dados["recorrencia_id"], dados["competencia_ocorrencia"])
        if chave in registros:
            return SimpleNamespace(data=[])
        registros[chave] = dados
        return SimpleNamespace(data=[dados])

    monkeypatch.setattr(transaction_service, "inserir_ocorrencia_recorrencia", inserir)
    recorrencia = _recorrencia_persistida()

    primeira = service.materializar_recorrencia(recorrencia, 2026, "OUTUBRO")
    segunda = service.materializar_recorrencia(recorrencia, 2026, "OUTUBRO")

    assert primeira["criada"] is True
    assert segunda["criada"] is False
    assert segunda["existente"] is True
    assert len(registros) == 1


def test_sincronizar_recorrencias_retorna_resumo_minimo(monkeypatch):
    registros = {}

    def inserir(dados):
        chave = (dados["recorrencia_id"], dados["competencia_ocorrencia"])
        if chave in registros:
            return SimpleNamespace(data=[])
        registros[chave] = dados
        return SimpleNamespace(data=[dados])

    monkeypatch.setattr(
        service,
        "listar_recorrencias",
        lambda: pd.DataFrame(
            [
                _recorrencia_persistida(id=42),
                _recorrencia_persistida(id=43, status_recorrencia="Pausada"),
            ]
        ),
    )
    monkeypatch.setattr(transaction_service, "inserir_ocorrencia_recorrencia", inserir)

    primeira = service.sincronizar_recorrencias(2026, "OUTUBRO")
    segunda = service.sincronizar_recorrencias(2026, "OUTUBRO")

    assert primeira == {"criadas": 1, "existentes": 0, "nao_elegiveis": 1}
    assert segunda == {"criadas": 0, "existentes": 1, "nao_elegiveis": 1}
