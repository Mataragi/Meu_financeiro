import pandas as pd

from services.supabase_client import supabase


# =========================
# DÍVIDAS INFORMAIS
# =========================

def inserir_divida_informal(dados):
    supabase.table("dividas_informais").insert(dados).execute()


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
    supabase.table("dividas_informais").update(dados).eq("id", id_divida).execute()


def excluir_divida_informal(id_divida):
    supabase.table("dividas_informais").delete().eq("id", id_divida).execute()


# =========================
# TRANSAÇÕES
# =========================

def inserir_dados(dados):
    supabase.table("transacoes").insert(dados).execute()


def gerar_backup_transacoes():
    res = supabase.table("transacoes").select("*").execute()

    if not res.data:
        return None

    return pd.DataFrame(res.data).to_csv(index=False).encode("utf-8")


def carregar_dados(mes, ano=None):
    query = supabase.table("transacoes").select("*")

    if ano is not None:
        query = query.eq("ano", ano)

    if mes != "TODOS":
        query = query.eq("mes", mes)

    res = query.execute()
    return pd.DataFrame(res.data)


def atualizar_registro(id_registro, dados):
    supabase.table("transacoes").update(dados).eq("id", id_registro).execute()


def atualizar_status_registro(id_registro, status):
    supabase.table("transacoes").update({"status": status}).eq("id", id_registro).execute()


def atualizar_status_multiplos(ids, status):
    supabase.table("transacoes").update({"status": status}).in_("id", ids).execute()


def excluir_registro(id_registro):
    supabase.table("transacoes").delete().eq("id", id_registro).execute()


def excluir_multiplos(ids):
    supabase.table("transacoes").delete().in_("id", ids).execute()


def excluir_multiplos_do_mes(ids, mes):
    supabase.table("transacoes") \
        .delete() \
        .eq("mes", mes) \
        .in_("id", ids) \
        .execute()


def excluir_grupo_parcelamento(grupo_id):
    supabase.table("transacoes") \
        .delete() \
        .eq("grupo_parcelamento", grupo_id) \
        .execute()


def excluir_mes(mes, ano):
    supabase.table("transacoes").delete().eq("mes", mes).eq("ano", ano).execute()


def carregar_dados_mes(mes, ano):
    res = (
        supabase
        .table("transacoes")
        .select("*")
        .eq("mes", mes)
        .eq("ano", ano)
        .execute()
    )
    return res.data
