import streamlit as st
from datetime import datetime
from services.database import (
    inserir_dados,
    carregar_dados,
    dar_baixa_multiplos,
    excluir_multiplos
)

def formatar_data(valor):
    try:
        # se vier como string ISO (ex: 2026-04-25T10:30:00)
        dt = datetime.fromisoformat(valor.replace("Z",""))
        return dt.strftime("%d/%m")
    except:
        return ""  # fallback

def render_mobile():

    mes = st.selectbox(
        "📅 Mês",
        ["Selecione","TODOS", "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"],
        key="mes_mobile"
    )

    status_view = st.selectbox(
    "Status",
    ["selecione", "Pendentes", "Pagos"],
    key="status_view_mobile"
    )

    df = carregar_dados(mes)

    if not df.empty:
        if status_view == "Pendentes":
            df = df[df["status"].str.lower() == "pendente"]
        elif status_view == "Pagos":
            df = df[df["status"].str.lower() == "pago"]

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
    if "show_form" not in st.session_state:
        st.session_state.show_form = False

    if st.button("➕ Nova Transação", use_container_width=True):
        st.session_state.show_form = not st.session_state.show_form

    # Formulário
    if st.session_state.get("show_form", False):
        with st.form("nova_transacao"):
            desc = st.text_input("Descrição")
            valor = st.number_input("Valor", min_value=0.0)
            tipo = st.selectbox("Tipo", ["Saída","Entrada"])
            status = st.selectbox("Status", ["Pendente","Pago"])

            salvar = st.form_submit_button("💾 Salvar", use_container_width=True)

            if salvar:
                if not desc.strip():
                    st.error("Informe uma descrição.")
                elif valor <= 0:
                    st.error("")
                else:
                    inserir_dados([{
                        "mes": mes,
                        "descricao": desc,
                        "valor": valor,
                        "tipo": tipo,
                        "status": status
                    }])

                    st.success("Salvo!")
                    st.session_state.show_form = False
                    st.rerun()

    st.divider()

    st.subheader("Ações")

    with st.expander("✅ Dar baixa"):
        df_pendentes = carregar_dados(mes)

        if not df_pendentes.empty:
            df_pendentes = df_pendentes[df_pendentes["status"].str.lower() == "pendente"]

            opcoes_baixa = {}

            for _, row in df_pendentes.iterrows():
                valor = float(row.get("valor", 0))
                valor_fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                data = formatar_data(str(row.get("criado_em", "")))
                label = f"{row.get('descricao', '')} — {valor_fmt} · {data}"
                opcoes_baixa[label] = row.get("id")

            selecionados_baixa = st.multiselect(
                "Selecionar pendentes",
                list(opcoes_baixa.keys()),
                key="selecionados_baixa_mobile"
            )

            ids_baixa = [opcoes_baixa[item] for item in selecionados_baixa]

            if st.button("✅ Confirmar baixa", use_container_width=True):
                dar_baixa_multiplos(ids_baixa)
        else:
            st.info("Nenhuma pendência encontrada.")

    with st.expander("🗑️ Excluir registros"):
        
        if mes == "TODOS":
            st.warning("Selecione um mês específico para excluir registros. Exclusão em TODOS está bloqueada por segurança.")
        
        else:
            df_excluir = carregar_dados(mes)

            if not df_excluir.empty:
                opcoes_excluir = {}

                for _, row in df_excluir.iterrows():
                    valor = float(row.get("valor", 0))
                    valor_fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    data = formatar_data(str(row.get("criado_em", "")))
                    label = f"{row.get('descricao', '')} — {valor_fmt} · {row.get('status', '')} · {data}"
                    opcoes_excluir[label] = row.get("id")

                selecionados_excluir = st.multiselect(
                    "Selecionar registros",
                    list(opcoes_excluir.keys()),
                    key="selecionados_excluir_mobile"
                )

                ids_excluir = [opcoes_excluir[item] for item in selecionados_excluir]

                if st.button("🗑️ Confirmar exclusão", use_container_width=True):
                    excluir_multiplos(ids_excluir)
            else:
                st.info("Nenhum registro encontrado.")

        st.divider()

    st.subheader("Transações")

    if mes == "Selecione" or status_view == "Selecione":
        st.info("Selecione um MÊS e um STATUS para visualizar os registros.")
    else:
        df_lista = carregar_dados(mes)

        if not df_lista.empty:
            if status_view == "Pendentes":
                df_lista = df_lista[df_lista["status"].str.lower() == "pendente"]
            elif status_view == "Pagos":
                df_lista = df_lista[df_lista["status"].str.lower() == "pago"]

            if not df_lista.empty:
                for _, row in df_lista.iterrows():
                    status = str(row.get("status", "")).lower()
                    cor = "🟢" if status == "pago" else "🔴"

                    valor = float(row.get("valor", 0))
                    valor_fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

                    tipo = row.get("tipo", "")
                    data = formatar_data(str(row.get("criado_em", "")))

                    st.markdown(f"""
{cor} **{row.get("descricao", "")}**

{valor_fmt} · {tipo} · {data}
""")
                    st.divider()
            else:
                st.info("Nenhum registro encontrado para esse filtro.")
        else:
            st.info("Nenhum registro encontrado.")