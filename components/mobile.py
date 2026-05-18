import streamlit as st
import pandas as pd
from datetime import datetime

from utils.formatacao import colorir_status, formatar_real
from services.database import (
    inserir_dados,
    inserir_parcelado,
    carregar_dados,
    dar_baixa_multiplos,
    excluir_multiplos,
    atualizar_registro
)


MESES = [
    "Selecione", "TODOS", "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL",
    "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO",
    "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
]

STATUS_VIEW = ["Selecione", "Todos", "Pendentes", "Pagos"]


def formatar_data(valor):
    try:
        dt = datetime.fromisoformat(str(valor).replace("Z", ""))
        return dt.strftime("%d/%m")
    except:
        return ""

def vencimento_seguro(valor):
    try:
        if pd.isna(valor):
            return 10
        return int(float(valor))
    except:
        return 10


def calcular_metricas(df_base):
    if df_base.empty:
        return 0, 0, 0

    df = df_base.copy()
    df["valor"] = df["valor"].astype(float)

    tipo = df["tipo"].astype(str).str.lower()
    status = df["status"].astype(str).str.lower()

    saidas = tipo.isin(["saida", "saída"])
    entradas = tipo == "entrada"

    pagos = df[(status == "pago") & saidas]["valor"].sum()
    pendentes = df[(status == "pendente") & saidas]["valor"].sum()
    entradas_total = df[entradas]["valor"].sum()

    saldo = entradas_total - pagos

    return pagos, pendentes, saldo


def filtrar_status(df, status_view):
    if df.empty:
        return df

    if status_view == "Pendentes":
        return df[df["status"].astype(str).str.lower() == "pendente"]

    if status_view == "Pagos":
        return df[df["status"].astype(str).str.lower() == "pago"]

    return df


def render_mobile():

    st.markdown("""
    <style>

    /* Remove campo de digitação do selectbox mobile */
    div[data-baseweb="select"] input {
        caret-color: transparent;
    }

    div[data-baseweb="select"] input:focus {
        outline: none !important;
    }

    /* Esconde cursor piscando */
    div[data-baseweb="select"] input {
        color: transparent !important;
        text-shadow: 0 0 0 white;
    }

    </style>
    """, unsafe_allow_html=True)

    ANOS = [2026, 2027, 2028, 2029, 2030]

    ano = st.selectbox("Ano", ANOS, key="ano_mobile")
    mes = st.selectbox("📅 Mês", MESES, key="mes_mobile")

    status_view = st.selectbox(
        "Status",
        STATUS_VIEW,
        key="status_view_mobile"
    )

    CATEGORIAS = [
        "Selecione", 
        "Sem categoria",
        "Mercado",
        "Casa",
        "Contas",
        "Transporte",
        "Alimentação",
        "Saúde",
        "Educação",
        "Lazer",
        "Família",
        "Cartão Crédito Luiz",
        "Dívida",
        "Outros"
    ]

    if mes == "Selecione":
        df_base = pd.DataFrame()
    else:
        df_base = carregar_dados(mes, ano)

    pagos, pendentes, saldo = calcular_metricas(df_base)

    c1, c2, c3 = st.columns(3)
    c1.metric("Pago", formatar_real(pagos))
    c2.metric("Pendente", formatar_real(pendentes))
    c3.metric("Saldo", formatar_real(saldo))

    st.divider()

    if "show_form" not in st.session_state:
        st.session_state.show_form = False

    if st.button("➕ Nova Transação", use_container_width=True):
        st.session_state.show_form = not st.session_state.show_form

    if st.session_state.get("show_form", False):
        with st.form("nova_transacao"):
            desc = st.text_input("Descrição")
            valor = st.number_input("Valor", min_value=0.0)
            categoria = st.selectbox("Categoria", CATEGORIAS)
            tipo = st.selectbox("Tipo", ["Saída", "Entrada"])
            status = st.selectbox("Status", ["Pendente", "Pago"])

            vencimento = st.number_input(
                "Dia do vencimento",
                min_value=1,
                max_value=31,
                value=10,
                step=1
            )

            
            total_parcelas = st.number_input(
                "Quantidade de parcelas",
                min_value=1,
                max_value=60,
                value=1,
                step=1
            )

            st.caption("Use 1 para compra à vista. Use 2 ou mais para parcelar.")

            salvar = st.form_submit_button("💾 Salvar", use_container_width=True)

            if salvar:
                if mes == "Selecione":
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
                        vencimento=vencimento
                    )

                    st.session_state.show_form = False
                    st.rerun()

    st.divider()

    st.subheader("Ações")

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
            else:
                opcoes_baixa = {}

                for _, row in df_pendentes.iterrows():
                    valor = float(row.get("valor", 0))
                    valor_fmt = formatar_real(valor)
                    data = formatar_data(row.get("criado_em", ""))
                    label = f"{row.get('descricao', '')} — {valor_fmt} · {data}"
                    opcoes_baixa[label] = row.get("id")

                selecionados_baixa = st.multiselect(
                    "Selecionar pendentes",
                    list(opcoes_baixa.keys()),
                    key="selecionados_baixa_mobile"
                )

                ids_baixa = [opcoes_baixa[item] for item in selecionados_baixa]

                if st.button("✅ Confirmar baixa", use_container_width=True):
                    if ids_baixa:
                        dar_baixa_multiplos(ids_baixa)
                    else:
                        st.warning("Selecione pelo menos um registro.")

    with st.expander("🗑️ Excluir registros"):
        if mes == "Selecione":
            st.warning("Selecione um mês para excluir registros.")
        elif df_base.empty:
            st.info("Nenhum registro encontrado.")
        else:
            opcoes_excluir = {}

            for _, row in df_base.iterrows():
                valor = float(row.get("valor", 0))
                valor_fmt = formatar_real(valor)
                data = formatar_data(row.get("criado_em", ""))
                label = f"{row.get('descricao', '')} — {valor_fmt} · {row.get('status', '')} · {data}"
                opcoes_excluir[label] = row.get("id")

            selecionados_excluir = st.multiselect(
                "Selecionar registros",
                list(opcoes_excluir.keys()),
                key="selecionados_excluir_mobile"
            )

            ids_excluir = [opcoes_excluir[item] for item in selecionados_excluir]

            if st.button("🗑️ Confirmar exclusão", use_container_width=True):
                if ids_excluir:
                    excluir_multiplos(ids_excluir)
                else:
                    st.warning("Selecione pelo menos um registro.")

    with st.expander("✏️ Editar registro"):
        if mes == "Selecione":
            st.info("Selecione um mês para editar registros.")
        elif df_base.empty:
            st.info("Nenhum registro encontrado.")
        else:
            opcoes_editar = {}

            for _, row in df_base.iterrows():
                valor = float(row.get("valor", 0))
                valor_fmt = formatar_real(valor)
                data = formatar_data(row.get("criado_em", ""))
                label = f"{row.get('descricao', '')} — {valor_fmt} · {row.get('status', '')} · {data}"
                opcoes_editar[label] = row.to_dict()

            registro_label = st.selectbox(
                "🔍 Buscar registro",
                ["Selecione"] + list(opcoes_editar.keys()),
                key="registro_editar_mobile"
            )

            if registro_label != "Selecione":
                registro = opcoes_editar[registro_label]

                nova_descricao = st.text_input(
                    "Descrição",
                    value=str(registro.get("descricao", "")),
                    key="edit_desc_mobile"
                )

                novo_valor = st.number_input(
                    "Valor",
                    min_value=0.0,
                    value=float(registro.get("valor", 0)),
                    key="edit_valor_mobile"
                )

                nova_categoria = st.selectbox(
                    "Categoria",
                    CATEGORIAS,
                    index=CATEGORIAS.index(registro.get("categoria", "Sem categoria"))
                    if registro.get("categoria", "Sem categoria") in CATEGORIAS else 1,
                    key="edit_categoria_mobile"
                )

                novo_status = st.selectbox(
                    "Status",
                    ["Pendente", "Pago"],
                    index=0 if str(registro.get("status", "")).lower() == "pendente" else 1,
                    key="edit_status_mobile"
                )

                novo_vencimento = st.number_input(
                    "Dia do vencimento",
                    min_value=1,
                    max_value=31,
                    value=int(registro.get("vencimento") or 10),
                    step=1,
                    key="edit_vencimento_mobile"
                )

                if st.button("💾 Salvar edição", use_container_width=True):
                    if not nova_descricao.strip():
                        st.error("Informe uma descrição.")
                    elif novo_valor <= 0 and novo_status == "Pago":
                        st.error("Registro pago precisa ter valor maior que zero.")
                    else:
                        atualizar_registro(
                            registro.get("id"),
                            {
                                "descricao": nova_descricao.strip(),
                                "valor": novo_valor,
                                "categoria": nova_categoria,
                                "status": novo_status,
                                "vencimento": novo_vencimento
                            }
                        )

    st.divider()

    st.subheader("Transações")

    if mes == "Selecione" or status_view == "Selecione":
        st.info("Selecione um MÊS e um STATUS para visualizar os registros.")
        return

    df_lista = filtrar_status(df_base.copy(), status_view)

    if df_lista.empty:
        st.info("Nenhum registro encontrado para esse filtro.")
        return
    
    if "categoria" not in df_lista.columns:
        df_lista["categoria"] = "Sem categoria"

    if "vencimento" not in df_lista.columns:
        df_lista["vencimento"] = ""

    df_mobile = df_lista[["descricao", "categoria", "valor", "status", "vencimento", "criado_em"]].copy()
    df_mobile["valor"] = df_mobile["valor"].astype(float)
    df_mobile["criado_em"] = pd.to_datetime(df_mobile["criado_em"]).dt.strftime("%d/%m")
    df_mobile["vencimento"] = df_mobile["vencimento"].apply(
    lambda x: "" if pd.isna(x) else str(int(float(x)))
    )
    
    st.dataframe(
        df_mobile
        .style.map(colorir_status, subset=["status"])
        .format({"valor": formatar_real}),
        use_container_width=True,
        hide_index=True,
        height=500
    )