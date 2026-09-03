import pandas as pd

from utils.status import STATUS_PAGO


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
            hist = str(row.iloc[1])
            entrada = str(row.iloc[3])
            saida = str(row.iloc[4])

            if saida not in ["nan", "0,00", "0", ""]:
                valor = abs(tratar_valor(saida))
                tipo = "saída"

            elif entrada not in ["nan", "0,00", "0", ""]:
                valor = tratar_valor(entrada)
                tipo = "entrada"

            else:
                continue

            registros.append(
                {
                    "mes": "ABRIL",
                    "descricao": hist,
                    "valor": valor,
                    "tipo": tipo,
                    "status": STATUS_PAGO,
                }
            )

        except (IndexError, ValueError, AttributeError):
            continue

    return registros