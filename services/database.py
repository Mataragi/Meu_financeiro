import pandas as pd
import streamlit as st
from services.supabase_client import supabase

def inserir_dados(dados):
    if dados:
        supabase.table("transacoes").insert(dados).execute()
        st.success(f"{len(dados)} registros enviados 🚀")

def carregar_dados(mes):
    if mes == "TODOS":
        res = supabase.table("transacoes").select("*").execute()
    else:
        res = supabase.table("transacoes").select("*").eq("mes", mes).execute()
    return pd.DataFrame(res.data)

def excluir_mes(mes):
    supabase.table("transacoes").delete().eq("mes", mes).execute()
    st.warning(f"{mes} foi limpo")
    st.rerun()

def clonar_mes(origem, destino):
    res = supabase.table("transacoes").select("*").eq("mes", origem).execute()

    if not res.data:
        st.warning("Nada pra copiar")
        return

    novos = [{
        "mes": destino,
        "descricao": i['descricao'],
        "valor": i['valor'],
        "tipo": i['tipo'],
        "status": "pendente"
    } for i in res.data]

    inserir_dados(novos)