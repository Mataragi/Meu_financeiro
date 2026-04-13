import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURAÇÃO SUPABASE ---
# Carrega as credenciais que você já configurou no secrets.toml
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def colorir_status(valor):
    # O .lower() aqui garante que a comparação ignore se é maiúsculo ou minúsculo
    if str(valor).lower() == 'pendente':
        return 'background-color: #ff4b4b; color: white' # Vermelho
    elif str(valor).lower() == 'pago':
        return 'background-color: #28a745; color: white' # Verde
    return ''

# Configuração da página
st.set_page_config(page_title="Meu Financeiro Pro", layout="wide")

# Mata a tradução automática
st.markdown('<html lang="pt-br">', unsafe_allow_html=True)
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

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
            dados = {
                "mes": mes_input,
                "descricao": desc,
                "valor": valor,
                "tipo": tipo,
                "status": status
            }
            supabase.table("transacoes").insert(dados).execute()
            st.success("Dados salvos no Supabase! 🚀")
            st.rerun()

# --- CLONAR MÊS ---
    st.divider()
    st.subheader("🚀 Replicar Mês")
    with st.expander("Copiar dados p/ outro mês"):
        origem = st.selectbox("Copiar de:", ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                                             "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"], key="origem")
        destino = st.selectbox("Para o mês:", ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                                               "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"], key="destino")
        
        if st.button("Confirmar Clonagem"):
            res = supabase.table("transacoes").select("*").eq("mes", origem).execute()
            if res.data:
                novos_dados = [{"mes": destino, "descricao": i['descricao'], "valor": i['valor'], 
                                "tipo": i['tipo'], "status": "pendente"} for i in res.data]
                supabase.table("transacoes").insert(novos_dados).execute()
                st.success(f"Dados de {origem} copiados para {destino}!")
                st.rerun()

# --- EXCLUIR MÊS INTEIRO ---
    st.divider()
    st.subheader("⚠️ Zona de Perigo")
    with st.expander("Excluir mês completo"):
        mes_excluir = st.selectbox("Mês para LIMPAR:", ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                                                        "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"], key="excluir_mes")
        confirmar = st.checkbox(f"Apagar tudo de {mes_excluir}?")
        if st.button("🚨 EXCLUIR TUDO"):
            if confirmar:
                supabase.table("transacoes").delete().eq("mes", mes_excluir).execute()
                st.warning(f"{mes_excluir} foi limpo!")
                st.rerun()

# --- FILTRO E DASHBOARD ---
mes_selecionado = st.selectbox("📅 Selecione o Mês:", 
                               ["TODOS", "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                                "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"], 
                               index=4)

if mes_selecionado == "TODOS":
    response = supabase.table("transacoes").select("*").execute()
else:
    response = supabase.table("transacoes").select("*").eq("mes", mes_selecionado).execute()

df = pd.DataFrame(response.data)

# --- EXIBIÇÃO E CÁLCULOS ---
if not df.empty:
    df['valor'] = pd.to_numeric(df['valor'])
    pagos = df[(df['status'].str.lower() == 'pago') & (df['tipo'].str.lower().isin(['saida', 'saída']))]['valor'].sum()
    pendentes = df[(df['status'].str.lower() == 'pendente') & (df['tipo'].str.lower().isin(['saida', 'saída']))]['valor'].sum()
    entradas = df[df['tipo'].str.lower() == 'entrada']['valor'].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Já Pago", f"R$ {pagos:,.2f}")
    col2.metric("A Pagar", f"R$ {pendentes:,.2f}")
    col3.metric("Saldo Real", f"R$ {entradas - pagos:,.2f}")

    st.divider()
    # 1. Converte o texto do banco para uma data real do Python
    df['criado_em'] = pd.to_datetime(df['criado_em'])

    # 2. Formata para o padrão brasileiro (Dia/Mês/Ano Hora:Minuto)
    df['criado_em'] = df['criado_em'].dt.strftime('%d/%m/%Y %H:%M')
    st.dataframe(df.style.map(colorir_status, subset=['status']).format({"valor": "R$ {:.2f}"}), use_container_width=True, hide_index=True)

    # --- PAGAMENTO RÁPIDO ---
    with st.expander("💸 Dar Baixa"):
        p_df = df[df['status'].str.lower() == 'pendente']
        if not p_df.empty:
            sel = st.multiselect("Pagar:", [f"{r['id']} - {r['descricao']}" for _, r in p_df.iterrows()])
            if st.button("✅ Confirmar"):
                ids = [int(s.split(' - ')[0]) for s in sel]
                supabase.table("transacoes").update({"status": "pago"}).in_("id", ids).execute()
                st.rerun()

    # --- FAXINA ---
    with st.expander("🛠️ Excluir em Lote"):
        opc = [f"{r['id']} - {r['descricao']}" for _, r in df.iterrows()]
        sel_del = st.multiselect("Deletar:", opc)
        if st.button("🗑️ Apagar"):
            ids_del = [int(s.split(' - ')[0]) for s in sel_del]
            supabase.table("transacoes").delete().in_("id", ids_del).execute()
            st.rerun()
else:
    st.info("Nada por aqui ainda.")