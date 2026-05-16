import streamlit as st
import pandas as pd

from services.database import inserir_dados, clonar_mes
from utils.processamento import ler_extrato, processar_extrato
from services.supabase_client import supabase


MESES = [
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
]

ANOS = [2026, 2027, 2028]


def gerar_backup():
    res = supabase.table("transacoes").select("*").execute()
    if not res.data:
        return None
    return pd.DataFrame(res.data).to_csv(index=False).encode("utf-8")


def tratar_backup(df):
    for c in ["id", "criado_em"]:
        if c in df.columns:
            df = df.drop(columns=[c])
    return df.to_dict(orient="records")


def render_sidebar():

    if "limpar_form" not in st.session_state:
        st.session_state.limpar_form = False

    with st.sidebar:
        st.header("💼 Controle")

        if st.session_state.limpar_form:
            st.session_state.desc_input = ""
            st.session_state.valor_input = 0.0
            st.session_state.tipo_input = "Saída"
            st.session_state.status_input = "Pendente"
            st.session_state.limpar_form = False

        ano = st.selectbox("Ano", ANOS, key="ano_input")
        mes = st.selectbox("Mês", MESES, key="mes_input")
        desc = st.text_input("Descrição", key="desc_input")
        valor = st.number_input("Valor", min_value=0.0, key="valor_input")
        tipo = st.radio("Tipo", ["Saída", "Entrada"], key="tipo_input")
        status = st.selectbox("Status", ["Pendente", "Pago"], key="status_input")

        if st.button("Salvar"):
            if not desc.strip():
                st.error("Informe uma descrição.")
            elif valor <= 0:
                st.error("Informe um valor maior que zero.")
            else:
                inserir_dados([{
                    "ano": ano,
                    "mes": mes,
                    "descricao": desc.strip(),
                    "valor": valor,
                    "tipo": tipo,
                    "status": status
                }])

                st.session_state.ano_filtro = ano
                st.session_state.mes_filtro = mes
                st.session_state.limpar_form = True

                st.rerun()

        st.divider()

        arq = st.file_uploader("Importar CSV", type="csv")
        if arq:
            df = ler_extrato(arq)
            st.write(df.head())

            if st.button("Processar CSV"):
                dados = processar_extrato(df)

                for item in dados:
                    item["ano"] = ano
                    item["mes"] = mes

                inserir_dados(dados)

        st.divider()

        st.subheader("🔄 Restaurar Backup")

        backup = st.file_uploader("Upload do backup (.csv)", type="csv", key="restore_backup")

        if backup:
            df = pd.read_csv(backup)
            st.write(df.head())

            if st.button("Restaurar Backup"):
                dados = tratar_backup(df)
                inserir_dados(dados)
                st.success("Backup restaurado com sucesso 🚀")
                st.rerun()

        st.divider()

        st.subheader("📋 Clonar mês")

        o_ano = st.selectbox("Ano origem:", ANOS, key="ano_origem_clone")
        o_mes = st.selectbox("Mês origem:", MESES, key="mes_origem_clone")

        d_ano = st.selectbox("Ano destino:", ANOS, key="ano_destino_clone")
        d_mes = st.selectbox("Mês destino:", MESES, key="mes_destino_clone")

        if st.button("Clonar Mês"):
            if o_ano == d_ano and o_mes == d_mes:
                st.warning("Origem e destino não podem ser iguais.")
            else:
                clonar_mes(o_mes, o_ano, d_mes, d_ano)

        st.divider()

        csv = gerar_backup()
        if csv:
            st.download_button("📥 Backup", csv, "backup.csv")

        st.divider()