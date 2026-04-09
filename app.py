import streamlit as st
import sqlite3
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Meu Financeiro Pro", layout="wide")

# Mata a tradução automática
st.markdown('<html lang="pt-br">', unsafe_allow_html=True)
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

def conectar():
    return sqlite3.connect('financeiro.db')

st.title("💰 Controle Financeiro Simples")

# --- FORMULÁRIO (Menu Lateral) ---
with st.sidebar:
    st.header("Novo Registro")
    mes_input = st.selectbox("Mês", ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                                     "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"])
    desc = st.text_input("Descrição")
    valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
    tipo = st.radio("Tipo", ["Saída", "Entrada"])
    status = st.selectbox("Status", ["Pendente", "Pago"])

    if st.button("Salvar no Banco"):
        if desc:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO transacoes (mes, descricao, valor, tipo, status) VALUES (?, ?, ?, ?, ?)",
                           (mes_input, desc, valor, tipo.lower(), status.lower()))
            conn.commit()
            conn.close()
            st.success("Dados salvos!")
            st.rerun()

# --- FILTRO E DASHBOARD ---
mes_selecionado = st.selectbox("📅 Selecione o Mês:", 
                               ["TODOS", "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                                "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"], 
                               index=4)

conn = conectar()
if mes_selecionado == "TODOS":
    df = pd.read_sql_query("SELECT * FROM transacoes", conn)
else:
    df = pd.read_sql_query(f"SELECT * FROM transacoes WHERE mes = '{mes_selecionado}'", conn)
conn.close()

# --- CÁLCULOS COM "DETECTOR DE ERROS" ---
if not df.empty:
    # Usamos .str.lower() para garantir que 'pago' ou 'PAGO' entrem na conta
    pagos = df[(df['status'].str.lower() == 'pago') & (df['tipo'].str.lower().isin(['saida', 'saída']))]['valor'].sum()
    pendentes = df[(df['status'].str.lower() == 'pendente') & (df['tipo'].str.lower().isin(['saida', 'saída']))]['valor'].sum()
    entradas = df[df['tipo'].str.lower() == 'entrada']['valor'].sum()
    
    saldo_real = entradas - pagos
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Já Pago (Saídas)", f"R$ {pagos:,.2f}")
    col2.metric("A Pagar (Saídas)", f"R$ {pendentes:,.2f}")
    col3.metric("Saldo Real", f"R$ {saldo_real:,.2f}")

    st.divider()
    st.subheader(f"Histórico - {mes_selecionado}")
    st.dataframe(df.style.format({"valor": "R$ {:.2f}"}), use_container_width=True)
    
    # --- PAGAMENTO RÁPIDO (Update de Status) ---
    st.divider()
    with st.expander("💸 Dar Baixa em Pendências"):
        # Filtramos apenas o que ainda não foi pago
        pendentes_df = df[df['status'].str.lower() == 'pendente']
        
        if not pendentes_df.empty:
            opcoes_pagar = [f"{row['id']} - {row['descricao']} (R$ {row['valor']})" for _, row in pendentes_df.iterrows()]
            selecionados_pagar = st.multiselect("Selecione o que você pagou:", options=opcoes_pagar)
            
            if st.button("✅ Confirmar Pagamento"):
                if selecionados_pagar:
                    ids_para_pagar = [int(item.split(' - ')[0]) for item in selecionados_pagar]
                    
                    conn = conectar()
                    cursor = conn.cursor()
                    # A mágica do UPDATE acontece aqui:
                    query = f"UPDATE transacoes SET status = 'pago' WHERE id IN ({','.join(map(str, ids_para_pagar))})"
                    cursor.execute(query)
                    conn.commit()
                    conn.close()
                    
                    st.success(f"Baixa confirmada para os itens: {ids_para_pagar}!")
                    st.rerun()
        else:
            st.write("🎉 Nenhuma conta pendente para este mês!")

    # --- FAXINA MULTISELEÇÃO ---
    st.divider()
    with st.expander("🛠️ Faxina nos Dados (Excluir em Lote)"):
        # Criamos uma lista formatada para facilitar a escolha
        opcoes = [f"{row['id']} - {row['descricao']} (R$ {row['valor']})" for _, row in df.iterrows()]
        selecionados_formatados = st.multiselect("Selecione os itens para deletar:", options=opcoes)
        
        if st.button("🗑️ Apagar Selecionados"):
            if selecionados_formatados:
                # Extraímos apenas o ID de volta da string formatada
                ids_para_deletar = [int(item.split(' - ')[0]) for item in selecionados_formatados]
                
                conn = conectar()
                cursor = conn.cursor()
                query = f"DELETE FROM transacoes WHERE id IN ({','.join(map(str, ids_para_deletar))})"
                cursor.execute(query)
                conn.commit()
                conn.close()
                st.warning(f"Registros {ids_para_deletar} removidos com sucesso!")
                st.rerun()
else:
    st.info("Nada por aqui ainda.")