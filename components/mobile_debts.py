import streamlit as st
import pandas as pd

from utils.formatacao import formatar_real
from services.database import (
    inserir_divida_informal,
    carregar_dividas_informais,
    atualizar_divida_informal,
    excluir_divida_informal
)


def render_mobile_debts():
    st.divider()
    st.subheader("🤝 Dívidas informais")

    with st.expander("➕ Nova dívida informal"):
        with st.form("nova_divida_informal"):
            pessoa = st.text_input("Pessoa")
            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor", min_value=0.0)
            tipo = st.selectbox("Tipo", ["Eu devo", "Me devem"])
            status = st.selectbox("Status", ["Pendente", "Pago"])
            observacao = st.text_area("Observação")

            salvar = st.form_submit_button("💾 Salvar dívida", use_container_width=True)

            if salvar:
                if not pessoa.strip():
                    st.error("Informe a pessoa.")
                elif not descricao.strip():
                    st.error("Informe a descrição.")
                else:
                    inserir_divida_informal([{
                        "pessoa": pessoa.strip(),
                        "descricao": descricao.strip(),
                        "valor": valor,
                        "tipo": tipo,
                        "status": status,
                        "observacao": observacao.strip()
                    }])

    df = carregar_dividas_informais()

    if df.empty:
        st.info("Nenhuma dívida informal cadastrada.")
        return

    st.markdown("### 📌 Pendências")

    df_view = df.copy()
    df_view["valor"] = df_view["valor"].astype(float)

    st.dataframe(
        df_view[["pessoa", "descricao", "valor", "tipo", "status", "observacao"]]
        .style
        .format({"valor": formatar_real}),
        use_container_width=True,
        hide_index=True,
        height=300
    )

    with st.expander("✏️ Editar dívida informal"):
        opcoes = {}

        for _, row in df.iterrows():
            valor_fmt = formatar_real(float(row.get("valor", 0)))
            label = f"{row.get('pessoa', '')} — {row.get('descricao', '')} — {valor_fmt} · {row.get('status', '')}"
            opcoes[label] = row.to_dict()

        escolhido = st.selectbox(
            "Selecionar dívida",
            ["Selecione"] + list(opcoes.keys()),
            key="editar_divida_informal"
        )

        if escolhido != "Selecione":
            registro = opcoes[escolhido]

            nova_pessoa = st.text_input(
                "Pessoa",
                value=str(registro.get("pessoa", "")),
                key="edit_divida_pessoa"
            )

            nova_descricao = st.text_input(
                "Descrição",
                value=str(registro.get("descricao", "")),
                key="edit_divida_descricao"
            )

            novo_valor = st.number_input(
                "Valor",
                min_value=0.0,
                value=float(registro.get("valor", 0)),
                key="edit_divida_valor"
            )

            novo_tipo = st.selectbox(
                "Tipo",
                ["Eu devo", "Me devem"],
                index=0 if registro.get("tipo") == "Eu devo" else 1,
                key="edit_divida_tipo"
            )

            novo_status = st.selectbox(
                "Status",
                ["Pendente", "Pago"],
                index=0 if registro.get("status") == "Pendente" else 1,
                key="edit_divida_status"
            )

            nova_observacao = st.text_area(
                "Observação",
                value=str(registro.get("observacao", "")),
                key="edit_divida_observacao"
            )

            if st.button("💾 Salvar alteração", use_container_width=True):
                atualizar_divida_informal(
                    registro.get("id"),
                    {
                        "pessoa": nova_pessoa.strip(),
                        "descricao": nova_descricao.strip(),
                        "valor": novo_valor,
                        "tipo": novo_tipo,
                        "status": novo_status,
                        "observacao": nova_observacao.strip()
                    }
                )

    with st.expander("🗑️ Excluir dívida informal"):
        opcoes_excluir = {}

        for _, row in df.iterrows():
            valor_fmt = formatar_real(float(row.get("valor", 0)))
            label = f"{row.get('pessoa', '')} — {row.get('descricao', '')} — {valor_fmt}"
            opcoes_excluir[label] = row.get("id")

        escolhido_excluir = st.selectbox(
            "Selecionar dívida para excluir",
            ["Selecione"] + list(opcoes_excluir.keys()),
            key="excluir_divida_informal"
        )

        if escolhido_excluir != "Selecione":
            if st.button("🗑️ Confirmar exclusão da dívida", use_container_width=True):
                excluir_divida_informal(opcoes_excluir[escolhido_excluir])