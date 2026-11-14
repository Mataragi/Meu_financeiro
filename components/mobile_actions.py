from datetime import date

import pandas as pd
import streamlit as st

from components.liquidacao_feedback import executar_liquidacao
from services.transaction_service import (
    dar_baixa_multiplos,
    liquidar_fatura_cartao,
    excluir_grupo_parcelamento,
    excluir_multiplos,
)
from utils.formatacao import formatar_valor_exibicao
from utils.status import STATUS_PENDENTE
from utils.tipo_transacao import TIPO_DESPESA


def _opcoes_registros(df, incluir_status=False):
    opcoes = {}

    for _, row in df.iterrows():
        valor_fmt = formatar_valor_exibicao(row.get("valor"))
        label = f"{row.get('descricao', '')} — {valor_fmt}"
        if incluir_status:
            label += f" · {row.get('status', '')}"
        opcoes[f"{label}"] = row

    return opcoes


def _render_baixa(df_base, mes):
    with st.expander("✅ Dar baixa"):
        if mes == "Selecione":
            st.info("Selecione um mês para dar baixa.")
            return
        if df_base.empty:
            st.info("Nenhuma pendência encontrada.")
            return

        df_pendentes = df_base[df_base["status"] == STATUS_PENDENTE].copy()
        if df_pendentes.empty:
            st.info("Nenhuma pendência encontrada.")
            return

        formas = (
            df_pendentes["forma_pagamento"].fillna("")
            if "forma_pagamento" in df_pendentes.columns
            else pd.Series("", index=df_pendentes.index)
        )
        credito = formas.astype(str).str.strip().str.casefold().isin(
            {"crédito", "credito"}
        )
        tipos = (
            df_pendentes["tipo"]
            if "tipo" in df_pendentes.columns
            else pd.Series(TIPO_DESPESA, index=df_pendentes.index)
        )
        despesas_credito = df_pendentes[credito & (tipos == TIPO_DESPESA)].copy()
        demais_pendencias = df_pendentes[~credito].copy()

        if "valor" in demais_pendencias.columns:
            sem_valor = demais_pendencias["valor"].isna().sum()
            demais_pendencias = demais_pendencias[demais_pendencias["valor"].notna()]
            if sem_valor:
                st.info("Transações sem valor não podem ser marcadas como pagas.")

        if not demais_pendencias.empty:
            st.markdown("**Baixa individual ou em lote**")
            opcoes = _opcoes_registros(demais_pendencias)
            selecionados = st.multiselect(
                "Selecionar pendentes",
                list(opcoes.keys()),
                key="selecionados_baixa_mobile",
            )
            ids = [opcoes[item].get("id") for item in selecionados]
            data_liquidacao = st.date_input(
                "Data efetiva do pagamento",
                value=date.today(),
                format="DD/MM/YYYY",
                key="data_liquidacao_mobile",
            )
            if st.button("✅ Confirmar baixa", use_container_width=True):
                if ids:
                    if executar_liquidacao(
                        lambda: dar_baixa_multiplos(ids, data_liquidacao),
                        f"{len(ids)} registro(s) liquidado(s).",
                    ):
                        st.rerun()
                else:
                    st.warning("Selecione pelo menos um registro.")

        if not despesas_credito.empty:
            st.divider()
            st.markdown("**💳 Pagar fatura de Crédito**")
            valores = pd.to_numeric(despesas_credito["valor"], errors="coerce")
            sem_valor = valores.isna().sum()
            despesas_credito = despesas_credito[valores.notna()].copy()
            despesas_credito["valor"] = valores[valores.notna()]
            if sem_valor:
                st.warning(
                    "Não é possível pagar a fatura enquanto houver compra de Crédito "
                    "sem valor informado. Corrija os lançamentos primeiro."
                )

            if despesas_credito.empty:
                st.info("Não há compras de Crédito com valor para liquidar.")
            elif sem_valor:
                st.metric("Compras pendentes", len(despesas_credito) + int(sem_valor))
                st.metric(
                    "Subtotal identificado",
                    formatar_valor_exibicao(float(despesas_credito["valor"].sum())),
                )
            else:
                total_fatura = float(despesas_credito["valor"].sum())
                st.metric("Compras pendentes", len(despesas_credito))
                st.metric("Total da fatura", formatar_valor_exibicao(total_fatura))
                st.caption(
                    "A baixa atualiza as compras existentes. Nenhuma nova despesa será criada."
                )
                data_fatura = st.date_input(
                    "Data efetiva do pagamento da fatura",
                    value=date.today(),
                    format="DD/MM/YYYY",
                    key="data_liquidacao_fatura_mobile",
                )
                if st.button(
                    "💳 Confirmar pagamento da fatura",
                    use_container_width=True,
                ):
                    ids_fatura = despesas_credito["id"].tolist()
                    if ids_fatura:
                        if executar_liquidacao(
                            lambda: liquidar_fatura_cartao(ids_fatura, data_fatura),
                            f"Fatura liquidada: {len(ids_fatura)} compra(s).",
                        ):
                            st.rerun()


def _render_exclusao(df_base, mes):
    with st.expander("🗑️ Excluir registros"):
        if mes == "Selecione":
            st.warning("Selecione um mês para excluir registros.")
        elif df_base.empty:
            st.info("Nenhum registro encontrado.")
        else:
            st.markdown("### 💳 Excluir parcelamento inteiro")
            df_parcelados = (
                pd.DataFrame()
                if "grupo_parcelamento" not in df_base.columns
                else df_base[df_base["grupo_parcelamento"].notna()]
            )
            if "recorrencia_id" in df_parcelados.columns:
                df_parcelados = df_parcelados[
                    df_parcelados["recorrencia_id"].isna()
                ]

            if df_parcelados.empty:
                st.info("Nenhum parcelamento encontrado neste filtro.")
            else:
                grupos = {}
                for _, row in df_parcelados.iterrows():
                    descricao = str(row.get("descricao", "")).rsplit(" ", 1)[0]
                    grupos[f"{descricao} — {row.get('total_parcelas', '')}x"] = row.get(
                        "grupo_parcelamento"
                    )

                escolhido = st.selectbox(
                    "Selecionar parcelamento",
                    ["Selecione"] + list(grupos.keys()),
                    key="grupo_delete_mobile",
                )
                if escolhido != "Selecione" and st.button(
                    "🗑️ Excluir parcelamento inteiro", use_container_width=True
                ):
                    excluir_grupo_parcelamento(grupos[escolhido])
                    st.warning("Parcelamento excluído 🗑️")
                    st.rerun()

            st.markdown("### 🧾 Excluir registros selecionados")
            df_excluiveis = df_base
            if "recorrencia_id" in df_base.columns:
                ocorrencias_recorrentes = df_base["recorrencia_id"].notna().sum()
                if ocorrencias_recorrentes:
                    st.info("Ocorrências recorrentes não podem ser excluídas.")
                df_excluiveis = df_base[df_base["recorrencia_id"].isna()]

            opcoes = _opcoes_registros(df_excluiveis, incluir_status=True)
            selecionados = st.multiselect(
                "Selecionar registros",
                list(opcoes.keys()),
                key="selecionados_excluir_mobile",
            )
            ids = [opcoes[item].get("id") for item in selecionados]

            if st.button("🗑️ Confirmar exclusão", use_container_width=True):
                if ids:
                    excluir_multiplos(ids)
                    st.warning(f"{len(ids)} registros excluídos 🗑️")
                    st.rerun()
                else:
                    st.warning("Selecione pelo menos um registro.")


def render_mobile_transaction_actions(df_base, mes):
    _render_baixa(df_base, mes)
    _render_exclusao(df_base, mes)
