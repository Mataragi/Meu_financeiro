import pandas as pd
import streamlit as st
from uuid import uuid4

from services.supabase_client import supabase


MESES_ORDEM = [
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
]


# =========================
# DÍVIDAS INFORMAIS
# =========================

def inserir_divida_informal(dados):
    if dados:
        supabase.table("dividas_informais").insert(dados).execute()
        st.cache_data.clear()
        st.success("Dívida informal registrada ✅")
        st.rerun()


@st.cache_data(ttl=30)
def carregar_dividas_informais():
    res = (
        supabase
        .table("dividas_informais")
        .select("*")
        .order("criado_em", desc=True)
        .execute()
    )
    return pd.DataFrame(res.data)


def atualizar_divida_informal(id_divida, dados):
    if id_divida and dados:
        supabase.table("dividas_informais").update(dados).eq("id", id_divida).execute()
        st.cache_data.clear()
        st.success("Dívida informal atualizada ✅")
        st.rerun()


def excluir_divida_informal(id_divida):
    if id_divida:
        supabase.table("dividas_informais").delete().eq("id", id_divida).execute()
        st.cache_data.clear()
        st.warning("Dívida informal excluída 🗑️")
        st.rerun()


# =========================
# TRANSAÇÕES
# =========================

def inserir_dados(dados):
    if dados:
        supabase.table("transacoes").insert(dados).execute()
        st.cache_data.clear()
        st.success(f"{len(dados)} registros enviados 🚀")


@st.cache_data(ttl=30)
def carregar_dados(mes, ano=None):
    query = supabase.table("transacoes").select("*")

    if ano is not None:
        query = query.eq("ano", ano)

    if mes != "TODOS":
        query = query.eq("mes", mes)

    res = query.execute()
    return pd.DataFrame(res.data)


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
            "status": "Pendente",
            "categoria": categoria,
            "parcela_atual": i + 1,
            "total_parcelas": total_parcelas,
            "grupo_parcelamento": grupo,
            "vencimento": vencimento,
        })

    inserir_dados(registros)


def atualizar_registro(id_registro, dados):
    if id_registro and dados:
        supabase.table("transacoes").update(dados).eq("id", id_registro).execute()
        st.cache_data.clear()
        st.success("Registro atualizado ✅")
        st.rerun()


def dar_baixa_registro(id_registro):
    if id_registro:
        supabase.table("transacoes").update({
            "status": "Pago"
        }).eq("id", id_registro).execute()

        st.cache_data.clear()
        st.success("Registro marcado como pago ✅")
        st.rerun()


def dar_baixa_multiplos(ids):
    if ids:
        supabase.table("transacoes").update({
            "status": "Pago"
        }).in_("id", ids).execute()

        st.cache_data.clear()
        st.success(f"{len(ids)} registros marcados como pagos ✅")
        st.rerun()


def excluir_registro(id_registro):
    if id_registro:
        supabase.table("transacoes").delete().eq("id", id_registro).execute()
        st.cache_data.clear()
        st.warning("Registro excluído 🗑️")
        st.rerun()


def excluir_multiplos(ids):
    if ids:
        supabase.table("transacoes").delete().in_("id", ids).execute()
        st.cache_data.clear()
        st.warning(f"{len(ids)} registros excluídos 🗑️")
        st.rerun()


def excluir_grupo_parcelamento(grupo_id):
    if grupo_id:
        supabase.table("transacoes") \
            .delete() \
            .eq("grupo_parcelamento", grupo_id) \
            .execute()

        st.cache_data.clear()
        st.warning("Parcelamento excluído 🗑️")
        st.rerun()


# =========================
# UTILIDADES DE MÊS
# =========================

def excluir_mes(mes, ano):
    supabase.table("transacoes").delete().eq("mes", mes).eq("ano", ano).execute()
    st.cache_data.clear()
    st.warning(f"{mes}/{ano} foi limpo")
    st.rerun()


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
        st.warning("Nada pra copiar")
        return

    novos = []

    for i in res.data:
        novos.append({
            "ano": destino_ano,
            "mes": destino_mes,
            "descricao": i["descricao"],
            "valor": i["valor"],
            "tipo": i["tipo"],
            "status": "pendente",
            "categoria": i.get("categoria", "Sem categoria"),
            "vencimento": i.get("vencimento"),
        })

    inserir_dados(novos)
    