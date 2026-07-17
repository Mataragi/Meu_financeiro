import pandas as pd
import streamlit as st

from components.mobile_constants import CATEGORIAS
from components.mobile_helpers import filtrar_status
from services.database import inserir_parcelado
from utils.formatacao import colorir_status, formatar_real


def render_mobile_transaction_form(ano, mes):
    if "show_form" not in st.session_state:
        st.session_state.show_form = False

    if st.button("➕ Nova Transação", use_container_width=True):
        st.session_state.show_form = not st.session_state.show_form

    if not st.session_state.get("show_form", False):
        return

    with st.form("nova_transacao"):
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0)
        categoria = st.selectbox("Categoria", CATEGORIAS)
        tipo = st.selectbox("Tipo", ["Saída", "Entrada"])
        status = st.selectbox("Status", ["Pendente", "Pago"])
        vencimento = st.number_input(
            "Dia do vencimento", min_value=1, max_value=31, value=10, step=1
        )
        total_parcelas = st.number_input(
            "Quantidade de parcelas", min_value=1, max_value=60, value=1, step=1
        )
        st.caption("Use 1 para compra à vista. Use 2 ou mais para parcelar.")

        salvar = st.form_submit_button("💾 Salvar", use_container_width=True)

        if not salvar:
            return

        if mes in ["Selecione", "TODOS"]:
            st.error("Selecione um mês específico para salvar.")
        elif not desc.strip():
            st.error("Informe uma descrição.")
        elif valor <= 0 and status == "Pago":
            st.error("Registro pago precisa ter valor maior que zero.")
        elif categoria == "Selecione":
            st.error("Selecione uma categoria.")
        else:
            inserir_parcelado(
                ano=ano,
                mes=mes,
                descricao=desc.strip(),
                valor_total=valor,
                tipo=tipo,
                status=status,
                categoria=categoria,
                total_parcelas=int(total_parcelas),
                vencimento=vencimento,
            )
            st.session_state.show_form = False
            st.rerun()


def render_mobile_transaction_list(df_base, mes, status_view):
    st.subheader("Transações")

    if mes == "Selecione" or status_view == "Selecione":
        st.info("Selecione um MÊS e um STATUS para visualizar os registros.")
        return

    busca = st.text_input(
        "🔍 Buscar transação", placeholder="Ex: carro, mercado, claro..."
    ).strip()
    df_lista = filtrar_status(df_base.copy(), status_view)

    if busca:
        df_lista = df_lista[
            df_lista["descricao"].astype(str).str.lower().str.contains(
                busca.lower(), na=False
            )
        ]

    if df_lista.empty:
        st.info("Nenhum registro encontrado para esse filtro.")
        return

    if "categoria" not in df_lista.columns:
        df_lista["categoria"] = "Sem categoria"
    if "vencimento" not in df_lista.columns:
        df_lista["vencimento"] = ""

    df_mobile = df_lista[
        ["descricao", "categoria", "valor", "status", "vencimento", "criado_em"]
    ].copy()
    df_mobile["valor"] = df_mobile["valor"].astype(float)
    df_mobile["criado_em"] = pd.to_datetime(df_mobile["criado_em"]).dt.strftime("%d/%m")
    df_mobile["vencimento"] = df_mobile["vencimento"].apply(
        lambda valor: "" if pd.isna(valor) else str(int(float(valor)))
    )

    st.dataframe(
        df_mobile.style.map(colorir_status, subset=["status"]).format(
            {"valor": formatar_real}
        ),
        use_container_width=True,
        hide_index=True,
        height=500,
    )
