from io import StringIO

import pandas as pd
import pytest

from utils.processamento import ler_extrato, processar_extrato, tratar_valor
from utils.status import STATUS_PAGO


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("1.234,56", 1234.56),
        ("100,00", 100.0),
    ],
)
def test_tratar_valor_brasileiro(valor, esperado):
    assert tratar_valor(valor) == esperado


def test_processar_extrato_identifica_entradas_saidas_e_ignora_linhas_vazias():
    df = pd.DataFrame(
        [
            ["01/04/2026", "Mercado", "", "0,00", "1.234,56"],
            ["02/04/2026", "Salário", "", "100,00", "0,00"],
            ["03/04/2026", "Sem valor", "", "0,00", "0,00"],
        ]
    )

    registros = processar_extrato(df)

    assert registros == [
        {
            "mes": "ABRIL",
            "descricao": "Mercado",
            "valor": 1234.56,
            "tipo": "saída",
            "status": STATUS_PAGO,
        },
        {
            "mes": "ABRIL",
            "descricao": "Salário",
            "valor": 100.0,
            "tipo": "entrada",
            "status": STATUS_PAGO,
        },
    ]


def test_processar_extrato_ignora_linha_invalida_sem_interromper_processamento():
    class DataFrameComLinhaInvalida:
        def iterrows(self):
            yield 0, pd.Series(["01/04/2026", "Incompleta"])
            yield 1, pd.Series(["02/04/2026", "Receita", "", "50,00", "0,00"])

    registros = processar_extrato(DataFrameComLinhaInvalida())

    assert registros == [
        {
            "mes": "ABRIL",
            "descricao": "Receita",
            "valor": 50.0,
            "tipo": "entrada",
            "status": STATUS_PAGO,
        }
    ]


def test_ler_extrato_encontra_cabecalho_data_fora_da_primeira_linha():
    arquivo = StringIO(
        "Relatório bancário;;;;\n"
        "Data;Descrição;Ignorar;Entrada;Saída\n"
        "01/04/2026;Salário;;100,00;0,00\n"
    )

    df = ler_extrato(arquivo)

    assert list(df.columns) == ["Data", "Descrição", "Ignorar", "Entrada", "Saída"]
    assert len(df) == 1
    assert df.iloc[0]["Descrição"] == "Salário"
