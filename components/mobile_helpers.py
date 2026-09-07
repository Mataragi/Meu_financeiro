from datetime import date, datetime

import pandas as pd

from utils.status import STATUS_PAGO, STATUS_PENDENTE


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
            return 10
        return int(float(valor))
    except (TypeError, ValueError):
        return 10


def calcular_metricas(df_base):
    if df_base.empty:
        return 0, 0, 0

    df = df_base.copy()
    df["valor"] = df["valor"].astype(float)

    tipo = df["tipo"].astype(str).str.lower()
    status = df["status"]

    saidas = tipo.isin(["saida", "saída"])
    entradas = tipo == "entrada"

    pagos = df[(status == STATUS_PAGO) & saidas]["valor"].sum()
    pendentes = df[(status == STATUS_PENDENTE) & saidas]["valor"].sum()
    entradas_total = df[entradas]["valor"].sum()

    return pagos, pendentes, entradas_total - pagos


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
