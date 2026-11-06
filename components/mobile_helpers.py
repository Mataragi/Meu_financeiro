from datetime import date, datetime

import pandas as pd

from utils.status import STATUS_PAGO, STATUS_PENDENTE
from utils.financeiro import calcular_saldo_real
from utils.categoria import CATEGORIAS_OFICIAIS
from utils.tipo_transacao import TIPO_DESPESA, TIPO_RECEITA, normalizar_tipos_dataframe


def formatar_data(valor):
    try:
        if isinstance(valor, (date, datetime)):
            return valor.strftime("%d/%m/%Y")

        dt = datetime.fromisoformat(str(valor).replace("Z", ""))
        return dt.strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return ""


def vencimento_seguro(valor):
    try:
        if pd.isna(valor):
            return None
        return int(float(valor))
    except (TypeError, ValueError):
        return None


def valor_seguro(valor):
    try:
        if pd.isna(valor):
            return None
        return float(valor)
    except (TypeError, ValueError):
        return None


def calcular_metricas(df_base, saldo_abertura=None):
    if df_base.empty:
        return 0, 0, calcular_saldo_real(
            df_base,
            saldo_abertura=0 if saldo_abertura is None else saldo_abertura,
        )

    df = df_base.copy()
    df = normalizar_tipos_dataframe(df)
    df["valor"] = df["valor"].astype(float)

    status = df["status"]

    saidas = df["tipo"] == TIPO_DESPESA
    entradas = df["tipo"] == TIPO_RECEITA

    pagos = df[(status == STATUS_PAGO) & saidas]["valor"].sum()
    pendentes = df[(status == STATUS_PENDENTE) & saidas]["valor"].sum()
    return pagos, pendentes, calcular_saldo_real(
        df,
        saldo_abertura=0 if saldo_abertura is None else saldo_abertura,
    )


def filtrar_status(df, status_view):
    if df.empty:
        return df

    if status_view == "Pendentes":
        return df[df["status"] == STATUS_PENDENTE]

    if status_view == "Pagos":
        return df[df["status"] == STATUS_PAGO]

    return df


def filtrar_forma_pagamento(df, forma_pagamento_view):
    if df.empty or forma_pagamento_view == "Todos":
        return df

    if forma_pagamento_view == "Não informado":
        if "forma_pagamento" not in df.columns:
            return df.iloc[0:0]
        return df[df["forma_pagamento"].isna()]

    if "forma_pagamento" not in df.columns:
        return df.iloc[0:0]

    return df[df["forma_pagamento"] == forma_pagamento_view]


def filtrar_categoria(df, categoria_view):
    if df.empty or categoria_view == "Todas":
        return df

    if "categoria" not in df.columns:
        return df.iloc[0:0]

    if categoria_view == "Sem categoria":
        return df[df["categoria"].isna() | (df["categoria"] == "Sem categoria")]

    return df[df["categoria"] == categoria_view]


def preparar_dados_grafico_categorias(df):
    """Agrupa despesas usando exclusivamente a taxonomia oficial atual."""
    if df.empty or "valor" not in df.columns:
        return pd.DataFrame(columns=["categoria", "valor"])

    dados = df.copy()
    if "tipo" in dados.columns:
        dados = dados[dados["tipo"] == TIPO_DESPESA]

    if dados.empty:
        return pd.DataFrame(columns=["categoria", "valor"])

    categorias_validas = set(CATEGORIAS_OFICIAIS)

    def normalizar_categoria_grafico(valor):
        if pd.isna(valor) or not str(valor).strip():
            return "Sem categoria"

        categoria = str(valor).strip()
        if categoria in categorias_validas:
            return categoria

        # Preserva categorias oficiais que receberam emojis em versões antigas.
        categoria_sem_prefixo = categoria.lstrip()
        while categoria_sem_prefixo and not categoria_sem_prefixo[0].isalnum():
            categoria_sem_prefixo = categoria_sem_prefixo[1:].lstrip()
        if categoria_sem_prefixo in categorias_validas:
            return categoria_sem_prefixo

        # Categorias removidas/desconhecidas não devem reaparecer no gráfico.
        return "Outros"

    dados["categoria"] = dados.get("categoria", pd.Series(index=dados.index, dtype="object"))
    dados["categoria"] = dados["categoria"].map(normalizar_categoria_grafico)
    dados["valor"] = pd.to_numeric(dados["valor"], errors="coerce").fillna(0)
    dados = dados[dados["valor"] > 0]

    return (
        dados.groupby("categoria", as_index=False)["valor"]
        .sum()
        .sort_values("valor", ascending=False)
        .reset_index(drop=True)
    )
