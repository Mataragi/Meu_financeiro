import pandas as pd

from utils.financeiro import calcular_saldo


def test_saldo_considera_entradas_e_apenas_saidas_pagas():
    df = pd.DataFrame(
        [
            {"tipo": "Entrada", "status": "Pago", "valor": 5000.0},
            {"tipo": "Saída", "status": "Pago", "valor": 1500.0},
            {"tipo": "Saída", "status": "Pendente", "valor": 800.0},
        ]
    )

    assert calcular_saldo(df) == 3500.0
