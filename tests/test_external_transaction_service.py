import pandas as pd
import pytest

from services import external_transaction_service as registrar
from services import chatgpt_bridge
from services.transaction_service import normalizar_data_transacao


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


class FakeTransactionService:
    MESES_ORDEM = registrar.transaction_service.MESES_ORDEM

    def __init__(self, registros=None):
        self.registros = registros or []
        self.inseridos = []
        self.consultas = []

    def carregar_dados(self, mes, ano):
        self.consultas.append((mes, ano))
        return pd.DataFrame(self.registros)

    def inserir_dados(self, dados):
        self.inseridos.append(dados)

    def normalizar_data_transacao(self, valor):
        return normalizar_data_transacao(valor)


def test_registra_payload_valido_reutilizando_transaction_service(monkeypatch):
    fake = FakeTransactionService()
    monkeypatch.setattr(registrar, "transaction_service", fake)

    assert registrar.registrar_transacao_externa(PAYLOAD) is True
    assert fake.inseridos == [[{**PAYLOAD, "status": "Pago"}]]


def test_status_e_normalizado(monkeypatch):
    fake = FakeTransactionService()
    monkeypatch.setattr(registrar, "transaction_service", fake)

    registrar.registrar_transacao_externa({**PAYLOAD, "status": " PENDENTE "})

    assert fake.inseridos[0][0]["status"] == "Pendente"


def test_credito_forca_status_pendente(monkeypatch):
    fake = FakeTransactionService()
    monkeypatch.setattr(registrar, "transaction_service", fake)

    registrar.registrar_transacao_externa(
        {**PAYLOAD, "forma_pagamento": "Crédito", "status": "Pago"}
    )

    assert fake.inseridos[0][0]["status"] == "Pendente"


@pytest.mark.parametrize(
    "alteracao",
    [
        {"descricao": ""},
        {"valor": 0},
        {"tipo": "Transferência"},
        {"mes": "MÊS INVÁLIDO"},
        {"vencimento": 32},
        {"status": "Em análise"},
        {"forma_pagamento": "Cheque"},
        {"data_transacao": "31/08/2026"},
    ],
)
def test_payload_invalido_e_rejeitado_sem_chamar_repository(monkeypatch, alteracao):
    fake = FakeTransactionService()
    monkeypatch.setattr(registrar, "transaction_service", fake)

    with pytest.raises(ValueError):
        registrar.registrar_transacao_externa({**PAYLOAD, **alteracao})

    assert fake.inseridos == []
    assert fake.consultas == []


def test_payload_com_campo_novo_ausente_e_rejeitado(monkeypatch):
    fake = FakeTransactionService()
    monkeypatch.setattr(registrar, "transaction_service", fake)

    payload = dict(PAYLOAD)
    payload.pop("forma_pagamento")

    with pytest.raises(ValueError, match="forma_pagamento"):
        registrar.registrar_transacao_externa(payload)

    assert fake.inseridos == []
    assert fake.consultas == []


def test_transacao_duplicada_nao_e_registrada(monkeypatch):
    fake = FakeTransactionService([PAYLOAD])
    monkeypatch.setattr(registrar, "transaction_service", fake)

    assert registrar.registrar_transacao_externa(PAYLOAD) is False
    assert fake.inseridos == []


def test_transacao_semelhante_mas_com_data_diferente_e_registrada(monkeypatch):
    fake = FakeTransactionService([PAYLOAD])
    monkeypatch.setattr(registrar, "transaction_service", fake)

    assert registrar.registrar_transacao_externa(
        {**PAYLOAD, "data_transacao": "2026-09-01"}
    ) is True
    assert len(fake.inseridos) == 1


def test_repository_so_recebe_payload_apos_validacao_e_deduplicacao(monkeypatch):
    fake = FakeTransactionService()
    monkeypatch.setattr(registrar, "transaction_service", fake)

    registrar.registrar_transacao_externa(PAYLOAD)

    assert len(fake.inseridos) == 1


def test_preparacao_valida_sem_persistir(monkeypatch):
    fake = FakeTransactionService()
    monkeypatch.setattr(registrar, "transaction_service", fake)

    proposta = registrar.preparar_transacao_externa(PAYLOAD)

    assert proposta == {"payload": {**PAYLOAD, "status": "Pago"}, "duplicada": False}
    assert fake.inseridos == []
    assert fake.consultas == [("SETEMBRO", 2026)]


def test_preparacao_identifica_duplicidade_sem_persistir(monkeypatch):
    fake = FakeTransactionService([PAYLOAD])
    monkeypatch.setattr(registrar, "transaction_service", fake)

    proposta = registrar.preparar_transacao_externa(PAYLOAD)

    assert proposta["duplicada"] is True
    assert fake.inseridos == []


def test_confirmacao_registra_proposta_valida(monkeypatch):
    fake = FakeTransactionService()
    monkeypatch.setattr(registrar, "transaction_service", fake)

    proposta = registrar.preparar_transacao_externa(PAYLOAD)
    assert fake.inseridos == []

    assert registrar.confirmar_transacao_externa(proposta) is True
    assert fake.inseridos == [[{**PAYLOAD, "status": "Pago"}]]


def test_confirmacao_revalida_e_impede_duplicidade(monkeypatch):
    fake = FakeTransactionService([PAYLOAD])
    monkeypatch.setattr(registrar, "transaction_service", fake)

    proposta = {"payload": dict(PAYLOAD), "duplicada": False}

    assert registrar.confirmar_transacao_externa(proposta) is False
    assert fake.inseridos == []
    assert len(fake.consultas) == 1


def test_confirmacao_rejeita_proposta_invalida(monkeypatch):
    fake = FakeTransactionService()
    monkeypatch.setattr(registrar, "transaction_service", fake)

    with pytest.raises(ValueError, match="Proposta"):
        registrar.confirmar_transacao_externa({})

    assert fake.inseridos == []
    assert fake.consultas == []


def test_ponte_chatgpt_prepara_sem_persistir(monkeypatch):
    chamadas = []

    def fake_preparar(payload):
        chamadas.append(payload)
        return {"payload": payload, "duplicada": False}

    monkeypatch.setattr(chatgpt_bridge, "preparar_transacao_externa", fake_preparar)

    proposta = chatgpt_bridge.receber_payload_chatgpt(PAYLOAD)

    assert proposta == {"payload": PAYLOAD, "duplicada": False}
    assert chamadas == [PAYLOAD]


def test_ponte_chatgpt_confirmacao_delega_para_registrador(monkeypatch):
    chamadas = []

    def fake_confirmar(proposta):
        chamadas.append(proposta)
        return True

    monkeypatch.setattr(chatgpt_bridge, "confirmar_transacao_externa", fake_confirmar)

    proposta = {"payload": PAYLOAD, "duplicada": False}
    assert chatgpt_bridge.confirmar_payload_chatgpt(proposta) is True
    assert chamadas == [proposta]
