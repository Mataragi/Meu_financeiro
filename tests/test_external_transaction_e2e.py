import pandas as pd

from services import chatgpt_bridge
from services import transaction_service


PAYLOAD = {
    "descricao": "PIX para Barbara Eloiza da Silva Costa",
    "valor": 28.50,
    "tipo": "Saída",
    "status": "pago",
    "mes": "SETEMBRO",
    "ano": 2026,
    "categoria": "Mercado",
    "vencimento": 1,
    "forma_pagamento": "PIX",
    "data_transacao": "2026-08-31",
}


class FakeRepository:
    def __init__(self, registros=None):
        self.registros = list(registros or [])
        self.inseridos = []

    def carregar_dados(self, mes, ano=None):
        registros = [
            registro
            for registro in self.registros
            if registro.get("mes") == mes
            and (ano is None or registro.get("ano") == ano)
        ]
        return pd.DataFrame(registros)

    def inserir_dados(self, dados):
        self.inseridos.extend(dados)
        self.registros.extend(dados)


def test_fluxo_chatgpt_ate_repository_sem_persistir_antes_da_confirmacao(monkeypatch):
    repository = FakeRepository()
    monkeypatch.setattr(transaction_service, "database", repository)

    proposta = chatgpt_bridge.receber_payload_chatgpt(PAYLOAD)

    assert proposta["duplicada"] is False
    assert proposta["payload"]["status"] == "Pago"
    assert repository.inseridos == []

    assert chatgpt_bridge.confirmar_payload_chatgpt(proposta) is True

    assert repository.inseridos == [proposta["payload"]]


def test_fluxo_chatgpt_bloqueia_duplicidade_na_confirmacao(monkeypatch):
    repository = FakeRepository([dict(PAYLOAD, status="Pago")])
    monkeypatch.setattr(transaction_service, "database", repository)

    proposta = chatgpt_bridge.receber_payload_chatgpt(PAYLOAD)

    assert proposta["duplicada"] is True
    assert repository.inseridos == []

    assert chatgpt_bridge.confirmar_payload_chatgpt(proposta) is False
    assert repository.inseridos == []


def test_fluxo_chatgpt_revalida_payload_antes_de_persistir(monkeypatch):
    repository = FakeRepository()
    monkeypatch.setattr(transaction_service, "database", repository)

    proposta = chatgpt_bridge.receber_payload_chatgpt(PAYLOAD)
    proposta["payload"]["valor"] = 0

    try:
        chatgpt_bridge.confirmar_payload_chatgpt(proposta)
    except ValueError as exc:
        assert "valor" in str(exc).lower()
    else:
        raise AssertionError("A confirmação deveria rejeitar a proposta alterada.")

    assert repository.inseridos == []
