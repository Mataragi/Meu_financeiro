import pandas as pd
import streamlit as st

from services.supabase_client import supabase
from services.transaction_service import (
    atualizar_status_transacoes,
    atualizar_transacao,
    calcular_mes_ano_parcela as calcular_mes_ano_parcela_service,
    carregar_transacoes,
    clonar_transacoes_mes,
    criar_transacoes,
    criar_transacoes_parceladas,
    dar_baixa_transacao,
    dar_baixa_transacoes,
)
from utils.status import (
    normalizar_status,
    normalizar_status_para_persistencia,
)


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
    return criar_transacoes(dados, _inserir_dados)


def _inserir_dados(dados):
    supabase.table("transacoes").insert(dados).execute()
    _invalidar_cache_consultas()


def gerar_backup_transacoes():
    res = supabase.table("transacoes").select("*").execute()

    if not res.data:
        return None

    return pd.DataFrame(res.data).to_csv(index=False).encode("utf-8")


@st.cache_data(ttl=30)
def carregar_dados(mes, ano=None):
    return carregar_transacoes(mes, ano, _carregar_dados)


def _carregar_dados(mes, ano=None):
    query = supabase.table("transacoes").select("*")

    if ano is not None:
        query = query.eq("ano", ano)

    if mes != "TODOS":
        query = query.eq("mes", mes)

    res = query.execute()
    return pd.DataFrame(res.data)


def calcular_mes_ano_parcela(mes_inicial, ano_inicial, incremento):
    return calcular_mes_ano_parcela_service(mes_inicial, ano_inicial, incremento)


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
    return criar_transacoes_parceladas(
        ano,
        mes,
        descricao,
        valor_total,
        tipo,
        status,
        categoria,
        total_parcelas,
        _inserir_dados,
        vencimento,
    )


def atualizar_registro(id_registro, dados):
    return atualizar_transacao(id_registro, dados, _atualizar_registro)


def _atualizar_registro(id_registro, dados):
    supabase.table("transacoes").update(dados).eq("id", id_registro).execute()
    _invalidar_cache_consultas()


def dar_baixa_registro(id_registro):
    return dar_baixa_transacao(id_registro, _atualizar_status_registro)


def _atualizar_status_registro(id_registro, status):
    supabase.table("transacoes").update({"status": status}).eq("id", id_registro).execute()
    _invalidar_cache_consultas()


def dar_baixa_multiplos(ids):
    return dar_baixa_transacoes(ids, _atualizar_status_multiplos)


def atualizar_status_multiplos(ids, status):
    return atualizar_status_transacoes(ids, status, _atualizar_status_multiplos)


def _atualizar_status_multiplos(ids, status):
    supabase.table("transacoes").update({"status": status}).in_("id", ids).execute()
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
    return clonar_transacoes_mes(
        origem_mes,
        origem_ano,
        destino_mes,
        destino_ano,
        _carregar_transacoes_mes,
        _inserir_dados,
    )


def _carregar_transacoes_mes(mes, ano):
    res = (
        supabase
        .table("transacoes")
        .select("*")
        .eq("mes", mes)
        .eq("ano", ano)
        .execute()
    )
    return res.data
