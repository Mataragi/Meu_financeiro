from datetime import date, datetime

import pandas as pd

from utils.status import STATUS_PAGO, STATUS_PENDENTE
from utils.financeiro import calcular_saldo_real
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


def calcular_metricas(df_base):
    if df_base.empty:
        return 0, 0, 0

    df = df_base.copy()
    df = normalizar_tipos_dataframe(df)
    df["valor"] = df["valor"].astype(float)

    status = df["status"]

    saidas = df["tipo"] == TIPO_DESPESA
    entradas = df["tipo"] == TIPO_RECEITA

    pagos = df[(status == STATUS_PAGO) & saidas]["valor"].sum()
    pendentes = df[(status == STATUS_PENDENTE) & saidas]["valor"].sum()
    return pagos, pendentes, calcular_saldo_real(df, saldo_abertura=0)


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
