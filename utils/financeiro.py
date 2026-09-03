from utils.status import STATUS_PAGO


def calcular_saldo(df):
    entradas = df[df["tipo"].str.lower() == "entrada"]["valor"].sum()
    saidas_pagas = df[
        (df["status"] == STATUS_PAGO)
        & (df["tipo"].str.lower().isin(["saida", "saída"]))
    ]["valor"].sum()

    return entradas - saidas_pagas
