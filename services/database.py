import pandas as pd
import streamlit as st
from uuid import uuid4

from services.supabase_client import supabase
from utils.status import (
    STATUS_PAGO,
    STATUS_PENDENTE,
    normalizar_status,
    normalizar_status_para_persistencia,
)


MESES_ORDEM = [
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
]


def _invalidar_cache_consultas():
    st.cache_data.clear()


def _normalizar_status_dados(dados):
    if "status" not in dados:
        return dados

    return {
        **dados,
        "status": normalizar_status_para_persistencia(dados["status"]),
    }


def _normalizar_status_dataframe(df):
    if "status" in df.columns:
        df["status"] = df["status"].map(normalizar_status)

    return df


# =========================
# DÍVIDAS INFORMAIS
# =========================

def inserir_divida_informal(dados):
    if dados:
        dados_normalizados = [_normalizar_status_dados(dado) for dado in dados]
        supabase.table("dividas_informais").insert(dados_normalizados).execute()
        _invalidar_cache_consultas()


@st.cache_data(ttl=30)
def carregar_dividas_informais():
    res = (
        supabase
        .table("dividas_informais")
        .select("*")
        .order("criado_em", desc=True)
        .execute()
    )
    return _normalizar_status_dataframe(pd.DataFrame(res.data))


def atualizar_divida_informal(id_divida, dados):
    if id_divida and dados:
        dados_normalizados = _normalizar_status_dados(dados)
        supabase.table("dividas_informais").update(dados_normalizados).eq("id", id_divida).execute()
        _invalidar_cache_consultas()


def excluir_divida_informal(id_divida):
    if id_divida:
        supabase.table("dividas_informais").delete().eq("id", id_divida).execute()
        _invalidar_cache_consultas()


# =========================
# TRANSAÇÕES
# =========================

def inserir_dados(dados):
    if dados:
        dados_normalizados = [_normalizar_status_dados(dado) for dado in dados]
        supabase.table("transacoes").insert(dados_normalizados).execute()
        _invalidar_cache_consultas()


def gerar_backup_transacoes():
    res = supabase.table("transacoes").select("*").execute()

    if not res.data:
        return None

    return pd.DataFrame(res.data).to_csv(index=False).encode("utf-8")


@st.cache_data(ttl=30)
def carregar_dados(mes, ano=None):
    query = supabase.table("transacoes").select("*")

    if ano is not None:
        query = query.eq("ano", ano)

    if mes != "TODOS":
        query = query.eq("mes", mes)

    res = query.execute()
    return _normalizar_status_dataframe(pd.DataFrame(res.data))


def calcular_mes_ano_parcela(mes_inicial, ano_inicial, incremento):
    if mes_inicial not in MESES_ORDEM:
        raise ValueError(f"Mês inválido para parcelamento: {mes_inicial}")

    indice_mes = MESES_ORDEM.index(mes_inicial)
    novo_indice_total = indice_mes + incremento

    novo_ano = int(ano_inicial) + (novo_indice_total // 12)
    novo_mes = MESES_ORDEM[novo_indice_total % 12]

    return novo_mes, novo_ano


def inserir_parcelado(
    ano,
    mes,
    descricao,
    valor_total,
    tipo,
    status,
    categoria,
    total_parcelas,
    vencimento=None
):
    if total_parcelas <= 1:
        inserir_dados([{
            "ano": ano,
            "mes": mes,
            "descricao": descricao,
            "valor": valor_total,
            "tipo": tipo,
            "status": status,
            "categoria": categoria,
            "parcela_atual": 1,
            "total_parcelas": 1,
            "grupo_parcelamento": None,
            "vencimento": vencimento,
        }])
        return

    grupo = str(uuid4())
    valor_parcela = round(valor_total / total_parcelas, 2)

    registros = []

    for i in range(total_parcelas):
        mes_parcela, ano_parcela = calcular_mes_ano_parcela(mes, ano, i)

        registros.append({
            "ano": ano_parcela,
            "mes": mes_parcela,
            "descricao": f"{descricao} {i + 1}/{total_parcelas}",
            "valor": valor_parcela,
            "tipo": tipo,
            "status": status,
            "categoria": categoria,
            "parcela_atual": i + 1,
            "total_parcelas": total_parcelas,
            "grupo_parcelamento": grupo,
            "vencimento": vencimento,
        })

    inserir_dados(registros)


def atualizar_registro(id_registro, dados):
    if id_registro and dados:
        dados_normalizados = _normalizar_status_dados(dados)
        supabase.table("transacoes").update(dados_normalizados).eq("id", id_registro).execute()
        _invalidar_cache_consultas()


def dar_baixa_registro(id_registro):
    if id_registro:
        supabase.table("transacoes").update({
            "status": STATUS_PAGO
        }).eq("id", id_registro).execute()

        _invalidar_cache_consultas()


def dar_baixa_multiplos(ids):
    if ids:
        supabase.table("transacoes").update({
            "status": STATUS_PAGO
        }).in_("id", ids).execute()

        _invalidar_cache_consultas()


def atualizar_status_multiplos(ids, status):
    if ids:
        supabase.table("transacoes").update({
            "status": normalizar_status_para_persistencia(status)
        }).in_("id", ids).execute()

        _invalidar_cache_consultas()


def excluir_registro(id_registro):
    if id_registro:
        supabase.table("transacoes").delete().eq("id", id_registro).execute()
        _invalidar_cache_consultas()


def excluir_multiplos(ids):
    if ids:
        supabase.table("transacoes").delete().in_("id", ids).execute()
        _invalidar_cache_consultas()


def excluir_multiplos_do_mes(ids, mes):
    if ids:
        supabase.table("transacoes") \
            .delete() \
            .eq("mes", mes) \
            .in_("id", ids) \
            .execute()

        _invalidar_cache_consultas()


def excluir_grupo_parcelamento(grupo_id):
    if grupo_id:
        supabase.table("transacoes") \
            .delete() \
            .eq("grupo_parcelamento", grupo_id) \
            .execute()

        _invalidar_cache_consultas()


# =========================
# UTILIDADES DE MÊS
# =========================

def excluir_mes(mes, ano):
    supabase.table("transacoes").delete().eq("mes", mes).eq("ano", ano).execute()
    _invalidar_cache_consultas()


def clonar_mes(origem_mes, origem_ano, destino_mes, destino_ano):
    res = (
        supabase
        .table("transacoes")
        .select("*")
        .eq("mes", origem_mes)
        .eq("ano", origem_ano)
        .execute()
    )

    if not res.data:
        return 0

    novos = []

    for registro in res.data:
        # A resposta do Supabase é tipada como JSON, que também pode conter
        # valores escalares ou nulos. Aqui só copiamos registros (objetos).
        if not isinstance(registro, dict):
            continue

        novos.append({
            "ano": destino_ano,
            "mes": destino_mes,
            "descricao": registro["descricao"],
            "valor": registro["valor"],
            "tipo": registro["tipo"],
            "status": STATUS_PENDENTE,
            "categoria": registro.get("categoria", "Sem categoria"),
            "vencimento": registro.get("vencimento"),
        })

    inserir_dados(novos)
    return len(novos)
