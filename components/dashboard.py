import streamlit as st
import pandas as pd
from services.transaction_service import (
    atualizar_status_multiplos,
    carregar_dados,
    excluir_multiplos_do_mes,
    gerar_backup_transacoes,
)
from utils.financeiro import calcular_saldo_real
from utils.formatacao import colorir_status, formatar_valor_exibicao
from utils.status import STATUS_PAGO, STATUS_PENDENTE
from utils.tipo_transacao import TIPO_DESPESA

MESES = ["TODOS","JANEIRO","FEVEREIRO","MARÇO","ABRIL","MAIO","JUNHO",
         "JULHO","AGOSTO","SETEMBRO","OUTUBRO","NOVEMBRO","DEZEMBRO"]

def gerar_backup():
    return gerar_backup_transacoes()

def render_dashboard():

    if "mes_filtro" not in st.session_state:
        st.session_state.mes_filtro = "TODOS"

    ANOS = [2026, 2027, 2028]

    ano = st.selectbox("Ano", ANOS, key="ano_filtro")
    mes = st.selectbox("📅 Mês", MESES, key="mes_filtro")

    df = carregar_dados(mes, ano)

    if df.empty:
        st.info("Nada ainda")
        return

    df['valor'] = pd.to_numeric(df['valor'], errors="coerce")

    pagos = df[(df['status'] == STATUS_PAGO) & (df['tipo'] == TIPO_DESPESA)]['valor'].sum()
    pend = df[(df['status'] == STATUS_PENDENTE) & (df['tipo'] == TIPO_DESPESA)]['valor'].sum()
    c1,c2,c3 = st.columns(3)
    c1.metric("Pago", f"R$ {pagos:,.2f}")
    c2.metric("Pendente", f"R$ {pend:,.2f}")
    c3.metric(
        "Saldo calculado",
        f"R$ {calcular_saldo_real(df):,.2f}",
    )

    df['criado_em'] = pd.to_datetime(df['criado_em']).dt.strftime('%d/%m/%y %H:%M')

    st.dataframe(
        df.drop(columns=['id'])
        .style.map(colorir_status, subset=['status'])
        .format({"valor": formatar_valor_exibicao}),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    col1, col2 = st.columns(2)

    # DAR BAIXA
    with col1:
        with st.expander("💸 Dar Baixa"):

            pend_df = df[df['status'] == STATUS_PENDENTE]
            pend_df_com_valor = pend_df[pend_df["valor"].notna()]
            if len(pend_df_com_valor) < len(pend_df):
                st.info("Transações sem valor não podem ser marcadas como pagas.")
            pend_df = pend_df_com_valor.sort_values(by="criado_em", ascending=False)

            opcoes = {
                f"{r['descricao']} | {formatar_valor_exibicao(r['valor'])} | {r['criado_em']}": r['id']
                for _, r in pend_df.iterrows()
            }

            sel = st.multiselect(
                "Selecionar:",
                list(opcoes.keys()),
                key="multi_dar_baixa"
            )

            if st.button("Pagar"):
                ids = [opcoes[s] for s in sel]
                if ids:
                    atualizar_status_multiplos(ids, STATUS_PAGO)
                    st.rerun()

    # EXCLUIR
    with col2:
        with st.expander("🗑️ Excluir Registros"):

            if mes == "TODOS":
                st.warning("Selecione um mês específico")
            else:
                df_excluiveis = df
                if "recorrencia_id" in df.columns:
                    ocorrencias_recorrentes = df["recorrencia_id"].notna().sum()
                    if ocorrencias_recorrentes:
                        st.info("Ocorrências recorrentes não podem ser excluídas.")
                    df_excluiveis = df[df["recorrencia_id"].isna()]

                opcoes = {
                    f"{r['descricao']} | {formatar_valor_exibicao(r['valor'])} | {r['criado_em']}": r['id']
                    for _, r in df_excluiveis.iterrows()
                }

                sel = st.multiselect(
                    "Selecionar:",
                    list(opcoes.keys()),
                    key="multi_excluir"
                )

                if st.button("Apagar"):
                    ids = [opcoes[s] for s in sel]

                    if ids:
                        excluir_multiplos_do_mes(ids, mes)

                        st.rerun()

 
