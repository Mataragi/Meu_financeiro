from utils.status import STATUS_PAGO
from utils.tipo_transacao import TIPO_DESPESA, TIPO_RECEITA, normalizar_tipos_dataframe


def calcular_saldo(df):
    df = normalizar_tipos_dataframe(df)
    entradas = df[df["tipo"] == TIPO_RECEITA]["valor"].sum()
    saidas_pagas = df[
        (df["status"] == STATUS_PAGO)
        & (df["tipo"] == TIPO_DESPESA)
    ]["valor"].sum()

    return entradas - saidas_pagas
