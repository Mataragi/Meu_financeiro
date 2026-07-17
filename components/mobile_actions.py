import pandas as pd
import streamlit as st

from components.mobile_constants import CATEGORIAS
from components.mobile_helpers import formatar_data, vencimento_seguro
from services.database import (
    atualizar_registro,
    dar_baixa_multiplos,
    excluir_grupo_parcelamento,
    excluir_multiplos,
)
from utils.formatacao import formatar_real


def _opcoes_registros(df, incluir_status=False):
    opcoes = {}

    for _, row in df.iterrows():
        valor_fmt = formatar_real(float(row.get("valor", 0)))
        data = formatar_data(row.get("criado_em", ""))
        label = f"{row.get('descricao', '')} — {valor_fmt}"
        if incluir_status:
            label += f" · {row.get('status', '')}"
        opcoes[f"{label} · {data}"] = row

    return opcoes


def _render_baixa(df_base, mes):
    with st.expander("✅ Dar baixa"):
        if mes == "Selecione":
            st.info("Selecione um mês para dar baixa.")
        elif df_base.empty:
            st.info("Nenhuma pendência encontrada.")
        else:
            df_pendentes = df_base[
                df_base["status"].astype(str).str.lower() == "pendente"
            ]
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
                else:
                    st.warning("Selecione pelo menos um registro.")


def _render_edicao(df_base, mes):
    with st.expander("✏️ Editar registro"):
        if mes == "Selecione":
            st.info("Selecione um mês para editar registros.")
        elif df_base.empty:
            st.info("Nenhum registro encontrado.")
        else:
            opcoes = _opcoes_registros(df_base, incluir_status=True)
            escolhido = st.selectbox(
                "🔍 Buscar registro",
                ["Selecione"] + list(opcoes.keys()),
                key="registro_editar_mobile",
            )
            if escolhido == "Selecione":
                return

            registro = opcoes[escolhido].to_dict()
            registro_id = registro.get("id")
            nova_descricao = st.text_input(
                "Descrição",
                value=str(registro.get("descricao", "")),
                key=f"edit_desc_mobile_{registro_id}",
            )
            novo_valor = st.number_input(
                "Valor",
                min_value=0.0,
                value=float(registro.get("valor", 0)),
                key=f"edit_valor_mobile_{registro_id}",
            )
            categoria_atual = registro.get("categoria", "Sem categoria")
            nova_categoria = st.selectbox(
                "Categoria",
                CATEGORIAS,
                index=CATEGORIAS.index(categoria_atual)
                if categoria_atual in CATEGORIAS
                else 1,
                key=f"edit_categoria_mobile_{registro_id}",
            )
            novo_status = st.selectbox(
                "Status",
                ["Pendente", "Pago"],
                index=0 if str(registro.get("status", "")).lower() == "pendente" else 1,
                key=f"edit_status_mobile_{registro_id}",
            )
            novo_vencimento = st.number_input(
                "Dia do vencimento",
                min_value=1,
                max_value=31,
                value=vencimento_seguro(registro.get("vencimento")),
                step=1,
                key=f"edit_vencimento_mobile_{registro_id}",
            )

            if st.button(
                "💾 Salvar edição",
                use_container_width=True,
                key=f"salvar_edit_mobile_{registro_id}",
            ):
                if not nova_descricao.strip():
                    st.error("Informe uma descrição.")
                elif novo_valor <= 0 and novo_status == "Pago":
                    st.error("Registro pago precisa ter valor maior que zero.")
                else:
                    atualizar_registro(
                        registro_id,
                        {
                            "descricao": nova_descricao.strip(),
                            "valor": novo_valor,
                            "categoria": nova_categoria,
                            "status": novo_status,
                            "vencimento": novo_vencimento,
                        },
                    )


def render_mobile_transaction_actions(df_base, mes):
    st.subheader("Ações")
    _render_baixa(df_base, mes)
    _render_exclusao(df_base, mes)
    _render_edicao(df_base, mes)
