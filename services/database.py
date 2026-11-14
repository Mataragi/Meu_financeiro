import pandas as pd

from services.supabase_client import supabase


TAMANHO_PAGINA_TRANSACOES = 500


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


def inserir_transacao_recorrencia(dados):
    """Insere uma ocorrência sem substituir outra ocorrência existente."""
    return (
        supabase
        .table("transacoes")
        .upsert(
            dados,
            on_conflict="recorrencia_id,competencia_ocorrencia",
            ignore_duplicates=True,
        )
        .execute()
    )


def inserir_recorrencia(dados):
    res = supabase.table("recorrencias").insert(dados).execute()
    return res.data[0] if res.data else None


def carregar_recorrencias():
    res = (
        supabase
        .table("recorrencias")
        .select("*")
        .order("criado_em", desc=True)
        .execute()
    )
    return pd.DataFrame(res.data)


def carregar_recorrencia(id_recorrencia):
    res = (
        supabase
        .table("recorrencias")
        .select("*")
        .eq("id", id_recorrencia)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def atualizar_recorrencia(id_recorrencia, dados):
    res = (
        supabase
        .table("recorrencias")
        .update(dados)
        .eq("id", id_recorrencia)
        .execute()
    )
    return res.data[0] if res.data else None


def gerar_backup_transacoes():
    dados = carregar_historico_completo()
    if dados.empty:
        return None
    return dados.to_csv(index=False).encode("utf-8")


def carregar_dados(mes, ano=None):
    query = supabase.table("transacoes").select("*")

    if ano is not None:
        query = query.eq("ano", ano)

    if mes != "TODOS":
        query = query.eq("mes", mes)

    res = query.execute()
    return pd.DataFrame(res.data)


def carregar_historico_completo(tamanho_pagina=TAMANHO_PAGINA_TRANSACOES):
    """Lê todas as transações em páginas estáveis, sem depender do limite REST.

    O Data API do Supabase pode limitar cada resposta. A paginação por chave
    (``id > ultimo_id``), ordenada por ``id``, evita perdas por deslocamento
    quando linhas são removidas durante a leitura. A leitura só termina após
    uma página vazia; por isso continua correta mesmo se o limite configurado
    no projeto for menor que ``tamanho_pagina``.
    """
    if isinstance(tamanho_pagina, bool) or not isinstance(tamanho_pagina, int):
        raise ValueError("Tamanho de página inválido.")
    if tamanho_pagina < 1:
        raise ValueError("Tamanho de página deve ser maior que zero.")

    registros = []
    ultimo_id = None
    while True:
        consulta = supabase.table("transacoes").select("*").order("id")
        if ultimo_id is not None:
            consulta = consulta.gt("id", ultimo_id)
        resposta = consulta.range(0, tamanho_pagina - 1).execute()
        pagina = resposta.data or []
        if not pagina:
            break
        registros.extend(pagina)
        ultimo_id = pagina[-1]["id"]

    return pd.DataFrame(registros)


def carregar_transacoes_por_ids(ids):
    if not ids:
        return []

    res = (
        supabase
        .table("transacoes")
        .select(
            "id, valor, status, mes, ano, tipo, forma_pagamento, "
            "data_liquidacao, recorrencia_id, competencia_ocorrencia"
        )
        .in_("id", ids)
        .execute()
    )
    return res.data or []


def carregar_transacoes_por_grupo_parcelamento(grupo_id):
    if grupo_id is None:
        return []

    res = (
        supabase
        .table("transacoes")
        .select("id, valor, status, recorrencia_id, competencia_ocorrencia")
        .eq("grupo_parcelamento", grupo_id)
        .execute()
    )
    return res.data or []


def atualizar_registro(id_registro, dados):
    supabase.table("transacoes").update(dados).eq("id", id_registro).execute()


def atualizar_status_registro(id_registro, status):
    if status == "Pago":
        raise ValueError(
            "Use liquidar_transacoes para registrar uma baixa com data efetiva."
        )
    supabase.table("transacoes").update({"status": status}).eq("id", id_registro).execute()


def atualizar_status_multiplos(ids, status):
    if status == "Pago":
        raise ValueError(
            "Use liquidar_transacoes para registrar uma baixa com data efetiva."
        )
    supabase.table("transacoes").update({"status": status}).in_("id", ids).execute()


def liquidar_transacoes(ids, data_liquidacao, dados_adicionais=None):
    """Liquida o lote em uma única transação PostgreSQL via RPC.

    A função SQL bloqueia e valida todos os registros antes da atualização.
    Qualquer divergência gera exceção dentro do banco e reverte a operação
    inteira, inclusive quando uma falha ocorre durante o UPDATE.
    """
    resposta = supabase.rpc(
        "liquidar_transacoes",
        {
            "p_ids": list(ids),
            "p_data_liquidacao": data_liquidacao,
            "p_atualizacoes": dados_adicionais or {},
        },
    ).execute()
    return resposta.data or []


# =========================
# CONFIGURAÇÃO DE DISPONIBILIDADE
# =========================

def carregar_configuracao_disponibilidade():
    res = (
        supabase
        .table("configuracao_disponibilidade")
        .select("id, saldo_inicial, data_base")
        .eq("id", 1)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def salvar_configuracao_disponibilidade(dados):
    """Cria ou atualiza a única configuração consolidada (id=1)."""
    res = (
        supabase
        .table("configuracao_disponibilidade")
        .upsert(dados, on_conflict="id")
        .execute()
    )
    return res.data[0] if res.data else None


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
