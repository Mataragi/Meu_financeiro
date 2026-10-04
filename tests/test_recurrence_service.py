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
