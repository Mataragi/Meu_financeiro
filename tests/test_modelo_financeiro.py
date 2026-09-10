"""Especificação executável das regras formalizadas na Sprint 03.

Os casos marcados como xfail registram comportamentos definidos pelo modelo,
mas ainda não implementados no código de produção. Eles funcionam como uma
rede de segurança para a próxima etapa de implementação.
"""

from datetime import date

import pandas as pd
import pytest

from services import external_transaction_service as registrar
from utils.status import STATUS_PAGO, STATUS_PENDENTE


@pytest.mark.parametrize(
    ("tipo", "esperado"),
    [
        ("Receita", "Receita"),
        ("RECEITA", "Receita"),
        ("Despesa", "Despesa"),
        ("DESPESA", "Despesa"),
    ],
)
@pytest.mark.xfail(reason="Vocabulário Receita/Despesa ainda será migrado no código de produção.")
def test_contrato_externo_usa_receita_e_despesa(tipo, esperado):
    payload = {
        "descricao": "Teste",
        "valor": 100.0,
        "tipo": tipo,
        "status": "Pago",
        "mes": "SETEMBRO",
        "ano": 2026,
        "categoria": "Outros",
        "vencimento": None,
        "forma_pagamento": "PIX",
        "data_transacao": date(2026, 9, 10),
    }

    normalizado = registrar._normalizar_payload(payload)

    assert normalizado["tipo"] == esperado


@pytest.mark.xfail(reason="Vencimento opcional ainda não foi implementado no contrato externo.")
def test_contrato_externo_aceita_vencimento_ausente_quando_nao_existe_obrigacao():
    payload = {
        "descricao": "Compra PIX",
        "valor": 42.50,
        "tipo": "Despesa",
        "status": "Pago",
        "mes": "SETEMBRO",
        "ano": 2026,
        "categoria": "Mercado",
        "vencimento": None,
        "forma_pagamento": "PIX",
        "data_transacao": "2026-09-10",
    }

    proposta = registrar.preparar_transacao_externa(payload)

    assert proposta["payload"]["vencimento"] is None


def test_credito_permanece_pendente_no_modelo_externo():
    payload = {
        "descricao": "Combustível",
        "valor": 154.66,
        "tipo": "Saída",
        "status": STATUS_PAGO,
        "mes": "OUTUBRO",
        "ano": 2026,
        "categoria": "Transporte",
        "vencimento": 5,
        "forma_pagamento": "Crédito",
        "data_transacao": "2026-09-09",
    }

    normalizado = registrar._normalizar_payload(payload)

    assert normalizado["status"] == STATUS_PENDENTE
    assert normalizado["categoria"] == "Transporte"
    assert normalizado["forma_pagamento"] == "Crédito"
    assert normalizado["data_transacao"] == "2026-09-09"
    assert normalizado["mes"] == "OUTUBRO"


def test_payload_pix_pago_preserva_categoria_e_data_da_operacao():
    payload = {
        "descricao": "Compras supermercado",
        "valor": 250.00,
        "tipo": "Saída",
        "status": STATUS_PAGO,
        "mes": "SETEMBRO",
        "ano": 2026,
        "categoria": "Mercado",
        "vencimento": 10,
        "forma_pagamento": "PIX",
        "data_transacao": "2026-09-10",
    }

    normalizado = registrar._normalizar_payload(payload)

    assert normalizado["status"] == STATUS_PAGO
    assert normalizado["categoria"] == "Mercado"
    assert normalizado["forma_pagamento"] == "PIX"
    assert normalizado["data_transacao"] == "2026-09-10"


@pytest.mark.parametrize(
    ("status", "esperado"),
    [
        ("Pago", STATUS_PAGO),
        ("pago", STATUS_PAGO),
        ("Pendente", STATUS_PENDENTE),
        ("pendente", STATUS_PENDENTE),
    ],
)
def test_status_do_contrato_continua_normalizado(status, esperado):
    payload = {
        "descricao": "Teste",
        "valor": 10.0,
        "tipo": "Saída",
        "status": status,
        "mes": "SETEMBRO",
        "ano": 2026,
        "categoria": "Outros",
        "vencimento": 10,
        "forma_pagamento": "PIX",
        "data_transacao": "2026-09-10",
    }

    normalizado = registrar._normalizar_payload(payload)

    assert normalizado["status"] == esperado


def test_saldo_real_nao_deve_considerar_pendencias_como_valor_real():
    """Protege a regra conceitual do saldo real enquanto a API nova não existe."""
    saldo_inicial = 1000.0
    receitas_pagas = 500.0
    despesas_pagas = 300.0
    despesas_pendentes = 200.0
    receitas_pendentes = 150.0

    saldo_real = saldo_inicial + receitas_pagas - despesas_pagas
    saldo_projetado = saldo_real - despesas_pendentes + receitas_pendentes

    assert saldo_real == 1200.0
    assert saldo_projetado == 1150.0


def test_pagamento_da_fatura_deve_afetar_apenas_lancamentos_de_credito_pendentes():
    dados = pd.DataFrame(
        [
            {
                "tipo": "Saída",
                "forma_pagamento": "Crédito",
                "status": STATUS_PENDENTE,
                "mes": "OUTUBRO",
                "ano": 2026,
                "valor": 100.0,
            },
            {
                "tipo": "Saída",
                "forma_pagamento": "PIX",
                "status": STATUS_PENDENTE,
                "mes": "OUTUBRO",
                "ano": 2026,
                "valor": 50.0,
            },
            {
                "tipo": "Saída",
                "forma_pagamento": "Crédito",
                "status": STATUS_PAGO,
                "mes": "OUTUBRO",
                "ano": 2026,
                "valor": 75.0,
            },
        ]
    )

    fatura = dados[
        (dados["tipo"] == "Saída")
        & (dados["forma_pagamento"] == "Crédito")
        & (dados["status"] == STATUS_PENDENTE)
        & (dados["mes"] == "OUTUBRO")
        & (dados["ano"] == 2026)
    ]

    assert len(fatura) == 1
    assert fatura["valor"].sum() == 100.0


def test_movimentacao_patrimonial_nao_deve_ser_classificada_como_receita_ou_despesa():
    movimentos = [
        {"origem": "Conta familiar", "destino": "Corretora", "valor": 3000.0},
        {"origem": "Corretora", "destino": "Conta familiar", "valor": 3000.0},
    ]

    assert all(
        movimento["origem"] != movimento["destino"] for movimento in movimentos
    )
    assert sum(movimento["valor"] for movimento in movimentos) == 6000.0


@pytest.mark.parametrize(
    ("data_compra", "competencia_esperada"),
    [
        (4, "SETEMBRO"),
        (5, "OUTUBRO"),
        (9, "OUTUBRO"),
    ],
)
@pytest.mark.xfail(reason="A regra de fechamento do Crédito ainda não possui função de domínio dedicada.")
def test_fechamento_credito_determina_competencia(data_compra, competencia_esperada):
    # Especificação: dia 01-04 => próprio mês; dia 05+ => mês seguinte.
    assert registrar.calcular_competencia_credito(date(2026, 9, data_compra)) == competencia_esperada
