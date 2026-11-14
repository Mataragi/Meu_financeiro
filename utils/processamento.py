from datetime import datetime

import pandas as pd

from utils.status import STATUS_PAGO
from utils.tipo_transacao import TIPO_DESPESA, TIPO_RECEITA


MESES = (
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
)


def tratar_valor(v):
    return float(v.replace(".", "").replace(",", "."))


def ler_extrato(arq):
    df = pd.read_csv(arq, sep=";", encoding="latin1", on_bad_lines="skip")

    # Alguns bancos exportam linhas antes do cabeçalho.
    # Procura a linha que contém "Data" e redefine o cabeçalho.
    if "Data" not in df.columns:
        for idx in range(len(df)):
            row = df.iloc[idx]

            if "Data" in str(row.values):
                df.columns = row
                df = df.iloc[idx + 1 :].reset_index(drop=True)
                break

    df.columns = df.columns.str.strip()

    if "Data" in df.columns:
        df = df.dropna(subset=["Data"])
        df = df[df["Data"].astype(str).str.contains("/")]

    return df


def processar_extrato(df):
    registros = []

    for _, row in df.iterrows():
        try:
            valor_data = row["Data"] if "Data" in row.index else row.iloc[0]
            data_origem = datetime.strptime(str(valor_data).strip(), "%d/%m/%Y").date()
            hist = str(row.iloc[1])
            entrada = str(row.iloc[3])
            saida = str(row.iloc[4])

            if saida not in ["nan", "0,00", "0", ""]:
                valor = abs(tratar_valor(saida))
                tipo = TIPO_DESPESA

            elif entrada not in ["nan", "0,00", "0", ""]:
                valor = tratar_valor(entrada)
                tipo = TIPO_RECEITA

            else:
                continue

            registros.append(
                {
                    "mes": MESES[data_origem.month - 1],
                    "ano": data_origem.year,
                    "descricao": hist,
                    "valor": valor,
                    "tipo": tipo,
                    "status": STATUS_PAGO,
                    "data_transacao": data_origem.isoformat(),
                    "data_liquidacao": data_origem.isoformat(),
                }
            )

        except (IndexError, KeyError, ValueError, AttributeError):
            continue

    return registros
