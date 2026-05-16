import pandas as pd
import streamlit as st
from services.supabase_client import supabase

def inserir_dados(dados):
    if dados:
        supabase.table("transacoes").insert(dados).execute()
        st.success(f"{len(dados)} registros enviados 🚀")

def carregar_dados(mes, ano=None):
    query = supabase.table("transacoes").select("*")

    if ano is not None:
        query = query.eq("ano", ano)

    if mes != "TODOS":
        query = query.eq("mes", mes)

    res = query.execute()
    return pd.DataFrame(res.data)

def excluir_mes(mes, ano):
    supabase.table("transacoes").delete().eq("mes", mes).eq("ano", ano).execute()
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
            "status": "pendente"
        })

    inserir_dados(novos)
def dar_baixa_registro(id_registro):
    supabase.table("transacoes").update({
        "status": "Pago"
    }).eq("id", id_registro).execute()
    st.success("Registro marcado como pago ✅")
    st.rerun()


def excluir_registro(id_registro):
    supabase.table("transacoes").delete().eq("id", id_registro).execute()
    st.warning("Registro excluído 🗑️")
    st.rerun()

def dar_baixa_multiplos(ids):
    if ids:
        supabase.table("transacoes").update({
            "status": "Pago"
        }).in_("id", ids).execute()
        st.success(f"{len(ids)} registros marcados como pagos ✅")
        st.rerun()


def excluir_multiplos(ids):
    if ids:
        supabase.table("transacoes").delete().in_("id", ids).execute()
        st.warning(f"{len(ids)} registros excluídos 🗑️")
        st.rerun()