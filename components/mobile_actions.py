import pandas as pd
import streamlit as st

from services.transaction_service import (
    dar_baixa_multiplos,
    excluir_grupo_parcelamento,
    excluir_multiplos,
)
from utils.formatacao import formatar_real
from utils.status import STATUS_PENDENTE


def _opcoes_registros(df, incluir_status=False):
    opcoes = {}

    for _, row in df.iterrows():
        valor_fmt = formatar_real(float(row.get("valor", 0)))
        label = f"{row.get('descricao', '')} — {valor_fmt}"
        if incluir_status:
            label += f" · {row.get('status', '')}"
        opcoes[f"{label}"] = row

    return opcoes


def _render_baixa(df_base, mes):
    with st.expander("✅ Dar baixa"):
        if mes == "Selecione":
            st.info("Selecione um mês para dar baixa.")
        elif df_base.empty:
            st.info("Nenhuma pendência encontrada.")
        else:
            df_pendentes = df_base[df_base["status"] == STATUS_PENDENTE]
            if df_pendentes.empty:
                st.info("Nenhuma pendência encontrada.")
                return

            opcoes = _opcoes_registros(df_pendentes)
            selecionados = st.multiselect(
                "Selecionar pendentes",
                list(opcoes.keys()),
                key="selecionados_baixa_mobile",
            )
            ids = [opcoes[item].get("id") for item in selecionados]

            if st.button("✅ Confirmar baixa", use_container_width=True):
                if ids:
                    dar_baixa_multiplos(ids)
                    st.success(f"{len(ids)} registros marcados como pagos ✅")
                    st.rerun()
                else:
                    st.warning("Selecione pelo menos um registro.")


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

            st.divider()
            st.markdown("### 🧾 Excluir registros selecionados")
            opcoes = _opcoes_registros(df_base, incluir_status=True)
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
    st.subheader("Ações (em lote)")
    _render_baixa(df_base, mes)
    _render_exclusao(df_base, mes)
