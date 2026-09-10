import pandas as pd

from utils.financeiro import calcular_saldo, calcular_saldo_projetado, calcular_saldo_real


def test_saldo_considera_entradas_e_apenas_saidas_pagas():
    df = pd.DataFrame(
        [
            {"tipo": "Entrada", "status": "Pago", "valor": 5000.0},
            {"tipo": "Saída", "status": "Pago", "valor": 1500.0},
            {"tipo": "Saída", "status": "Pendente", "valor": 800.0},
        ]
    )

    assert calcular_saldo(df) == 3500.0


def test_saldo_real_e_projetado_separam_realizado_de_pendencias():
    df = pd.DataFrame(
        [
            {"tipo": "Receita", "status": "Pago", "valor": 600.0},
            {"tipo": "Receita", "status": "Pendente", "valor": 200.0},
            {"tipo": "Despesa", "status": "Pago", "valor": 300.0},
            {"tipo": "Despesa", "status": "Pendente", "valor": 400.0},
        ]
    )

    assert calcular_saldo_real(df, saldo_abertura=1000.0) == 1300.0
    assert calcular_saldo_projetado(df, saldo_abertura=1000.0) == 1100.0


def test_saldo_real_cobre_abertura_negativa_e_saldo_negativo():
    df = pd.DataFrame(
        [{"tipo": "Despesa", "status": "Pago", "valor": 1200.0}]
    )

    assert calcular_saldo_real(df, saldo_abertura=-100.0) == -1300.0


def test_saldos_sem_transacoes():
    df = pd.DataFrame(columns=["tipo", "status", "valor"])

    assert calcular_saldo_real(df, saldo_abertura=1000.0) == 1000.0
    assert calcular_saldo_projetado(df, saldo_abertura=1000.0) == 1000.0


def test_saldo_real_e_projetado_com_apenas_receitas():
    df = pd.DataFrame(
        [
            {"tipo": "Receita", "status": "Pago", "valor": 600.0},
            {"tipo": "Receita", "status": "Pendente", "valor": 200.0},
        ]
    )

    assert calcular_saldo_real(df, saldo_abertura=1000.0) == 1600.0
    assert calcular_saldo_projetado(df, saldo_abertura=1000.0) == 1800.0


def test_saldo_real_e_projetado_com_apenas_despesas():
    df = pd.DataFrame(
        [
            {"tipo": "Despesa", "status": "Pago", "valor": 300.0},
            {"tipo": "Despesa", "status": "Pendente", "valor": 400.0},
        ]
    )

    assert calcular_saldo_real(df, saldo_abertura=1000.0) == 700.0
    assert calcular_saldo_projetado(df, saldo_abertura=1000.0) == 300.0


def test_saldo_aceita_tipos_historicos_e_ignora_fechamento():
    df = pd.DataFrame(
        [
            {"tipo": "Entrada", "status": "Pago", "valor": 600.0},
            {"tipo": "Saída", "status": "Pago", "valor": 300.0},
            {"tipo": "Fechamento", "status": "Pago", "valor": 9999.0},
        ]
    )

    assert calcular_saldo_real(df, saldo_abertura=1000.0) == 1300.0


def test_credito_pendente_nao_reduz_saldo_real_e_pago_reduz():
    pendente = pd.DataFrame(
        [{"tipo": "Despesa", "status": "Pendente", "valor": 400.0}]
    )
    pago = pd.DataFrame(
        [{"tipo": "Despesa", "status": "Pago", "valor": 400.0}]
    )

    assert calcular_saldo_real(pendente, saldo_abertura=1000.0) == 1000.0
    assert calcular_saldo_real(pago, saldo_abertura=1000.0) == 600.0


def test_saldo_de_mes_especifico_usa_apenas_o_periodo_recebido():
    df = pd.DataFrame(
        [
            {"mes": "SETEMBRO", "ano": 2026, "tipo": "Receita", "status": "Pago", "valor": 600.0},
            {"mes": "OUTUBRO", "ano": 2026, "tipo": "Despesa", "status": "Pago", "valor": 200.0},
        ]
    )

    setembro = df[df["mes"] == "SETEMBRO"]

    assert calcular_saldo_real(setembro, saldo_abertura=1000.0) == 1600.0


def test_saldo_de_todos_os_meses_mantem_o_ano_do_periodo_consultado():
    df = pd.DataFrame(
        [
            {"mes": "SETEMBRO", "ano": 2026, "tipo": "Receita", "status": "Pago", "valor": 600.0},
            {"mes": "OUTUBRO", "ano": 2026, "tipo": "Despesa", "status": "Pago", "valor": 200.0},
            {"mes": "JANEIRO", "ano": 2027, "tipo": "Receita", "status": "Pago", "valor": 900.0},
        ]
    )

    todos_2026 = df[df["ano"] == 2026]

    assert calcular_saldo_real(todos_2026, saldo_abertura=1000.0) == 1400.0
