import streamlit as st
import pandas as pd
from services.database import carregar_dados
from utils.formatacao import colorir_status, formatar_real
from services.supabase_client import supabase

MESES = ["TODOS","JANEIRO","FEVEREIRO","MARÇO","ABRIL","MAIO","JUNHO",
         "JULHO","AGOSTO","SETEMBRO","OUTUBRO","NOVEMBRO","DEZEMBRO"]

def gerar_backup():
    res = supabase.table("transacoes").select("*").execute()
    if not res.data:
        return None
    return pd.DataFrame(res.data).to_csv(index=False).encode('utf-8')

def render_dashboard():

    if "mes_filtro" not in st.session_state:
        st.session_state.mes_filtro = "TODOS"

    mes = st.selectbox("📅 Mês", MESES, key="mes_filtro")
    df = carregar_dados(mes)

    if df.empty:
        st.info("Nada ainda")
        return

    df['valor'] = pd.to_numeric(df['valor'])

    pagos = df[(df['status'].str.lower()=='pago') & (df['tipo'].str.lower().isin(['saida','saída']))]['valor'].sum()
    pend = df[(df['status'].str.lower()=='pendente') & (df['tipo'].str.lower().isin(['saida','saída']))]['valor'].sum()
    ent = df[df['tipo'].str.lower()=='entrada']['valor'].sum()

    c1,c2,c3 = st.columns(3)
    c1.metric("Pago", f"R$ {pagos:,.2f}")
    c2.metric("Pendente", f"R$ {pend:,.2f}")
    c3.metric("Saldo", f"R$ {ent-pagos:,.2f}")

    df['criado_em'] = pd.to_datetime(df['criado_em']).dt.strftime('%d/%m/%y %H:%M')

    st.dataframe(
        df.drop(columns=['id'])
        .style.map(colorir_status, subset=['status'])
        .format({"valor": formatar_real}),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    col1, col2 = st.columns(2)

    # DAR BAIXA
    with col1:
        with st.expander("💸 Dar Baixa"):

            pend_df = df[df['status'].str.lower()=='pendente']
            pend_df = pend_df.sort_values(by="criado_em", ascending=False)

            opcoes = {
                f"{r['descricao']} | {formatar_real(r['valor'])} | {r['criado_em']}": r['id']
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
                    supabase.table("transacoes").update({"status":"pago"}).in_("id",ids).execute()
                    st.rerun()

    # EXCLUIR
    with col2:
        with st.expander("🗑️ Excluir Registros"):

            if mes == "TODOS":
                st.warning("Selecione um mês específico")
            else:
                opcoes = {
                    f"{r['descricao']} | {formatar_real(r['valor'])} | {r['criado_em']}": r['id']
                    for _, r in df.iterrows()
                }

                sel = st.multiselect(
                    "Selecionar:",
                    list(opcoes.keys()),
                    key="multi_excluir"
                )

                if st.button("Apagar"):
                    ids = [opcoes[s] for s in sel]

                    if ids:
                        supabase.table("transacoes")\
                            .delete()\
                            .eq("mes", mes)\
                            .in_("id", ids)\
                            .execute()

                        st.rerun()

 
