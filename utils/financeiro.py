import pandas as pd

from utils.status import STATUS_PAGO, STATUS_PENDENTE, normalizar_status
from utils.tipo_transacao import TIPO_DESPESA, TIPO_RECEITA, normalizar_tipos_dataframe


def _preparar_dados_saldo(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["tipo", "status", "valor"])

    resultado = normalizar_tipos_dataframe(df)
    if "status" in resultado.columns:
        resultado = resultado.copy()
        resultado["status"] = resultado["status"].map(normalizar_status)
    if "valor" in resultado.columns:
        resultado["valor"] = pd.to_numeric(resultado["valor"], errors="coerce").fillna(0)
    return resultado


def calcular_saldo_real(df, saldo_abertura=0):
    """Calcula o dinheiro realizado, sem considerar valores pendentes."""
    dados = _preparar_dados_saldo(df)
    receitas_pagas = dados[
        (dados["tipo"] == TIPO_RECEITA)
        & (dados["status"] == STATUS_PAGO)
    ]["valor"].sum()
    despesas_pagas = dados[
        (dados["tipo"] == TIPO_DESPESA)
        & (dados["status"] == STATUS_PAGO)
    ]["valor"].sum()

    return saldo_abertura + receitas_pagas - despesas_pagas


def calcular_saldo_projetado(df, saldo_abertura=0):
    """Calcula o saldo real acrescido de receitas e despesas pendentes."""
    dados = _preparar_dados_saldo(df)
    saldo_real = calcular_saldo_real(dados, saldo_abertura)
    receitas_pendentes = dados[
        (dados["tipo"] == TIPO_RECEITA)
        & (dados["status"] == STATUS_PENDENTE)
    ]["valor"].sum()
    despesas_pendentes = dados[
        (dados["tipo"] == TIPO_DESPESA)
        & (dados["status"] == STATUS_PENDENTE)
    ]["valor"].sum()

    return saldo_real + receitas_pendentes - despesas_pendentes


def calcular_saldo(df):
    """Compatibilidade: calcula saldo real sem abertura persistida."""
    return calcular_saldo_real(df, saldo_abertura=0)

    return entradas - saidas_pagas
