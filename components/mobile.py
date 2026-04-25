import streamlit as st
from services.database import inserir_dados, carregar_dados

def render_mobile():
    st.title("💰 Financeiro")

    # Saldo
    df = carregar_dados("TODOS")

    if not df.empty:
        df['valor'] = df['valor'].astype(float)

        pagos = df[(df['status'].str.lower()=='pago') & (df['tipo'].str.lower().isin(['saida','saída']))]['valor'].sum()
        ent = df[df['tipo'].str.lower()=='entrada']['valor'].sum()

        saldo = ent - pagos
    else:
        pagos = ent = saldo = 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Pago", f"R$ {pagos:,.2f}")
    c2.metric("Entradas", f"R$ {ent:,.2f}")
    c3.metric("Saldo", f"R$ {saldo:,.2f}")

    st.divider()

    # Botão nova transação
    if st.button("➕ Nova Transação", use_container_width=True):
        st.session_state.show_form = True

    # Formulário
    if st.session_state.get("show_form", False):
        with st.form("nova_transacao"):
            desc = st.text_input("Descrição")
            valor = st.number_input("Valor", min_value=0.0)
            tipo = st.selectbox("Tipo", ["Saída","Entrada"])
            status = st.selectbox("Status", ["Pendente","Pago"])

            salvar = st.form_submit_button("Salvar")

            if salvar and desc:
                inserir_dados([{
                    "mes": "TODOS",
                    "descricao": desc,
                    "valor": valor,
                    "tipo": tipo,
                    "status": status
                }])

                st.success("Salvo!")
                st.session_state.show_form = False
                st.rerun()

    st.divider()

    st.subheader("Últimas transações")

    df = carregar_dados("TODOS")

    if not df.empty:
        df = df.tail(10)
        st.dataframe(df, use_container_width=True)