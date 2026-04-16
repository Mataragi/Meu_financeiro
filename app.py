import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONFIG SUPABASE ---
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase: Client = init_supabase()

# --- CONSTANTES ---
MESES = [
    "JANEIRO","FEVEREIRO","MARÇO","ABRIL","MAIO","JUNHO",
    "JULHO","AGOSTO","SETEMBRO","OUTUBRO","NOVEMBRO","DEZEMBRO"
]

# --- UTIL ---
def colorir_status(valor):
    if str(valor).lower() == 'pendente':
        return 'background-color: #ff4b4b; color: white'
    elif str(valor).lower() == 'pago':
        return 'background-color: #28a745; color: white'
    return ''

def formatar_real(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return valor

def tratar_valor(v):
    return float(v.replace('.', '').replace(',', '.'))

# --- BANCO ---
def inserir_dados(dados):
    if dados:
        supabase.table("transacoes").insert(dados).execute()
        st.success(f"{len(dados)} registros enviados 🚀")


# --- CSV ---
def ler_extrato(arq):
    df = pd.read_csv(arq, sep=';', encoding='latin1', on_bad_lines='skip')

    if 'Data' not in df.columns:
        for i, row in df.iterrows():
            if 'Data' in str(row.values):
                df.columns = df.iloc[i]
                df = df.iloc[i+1:].reset_index(drop=True)
                break

    df.columns = df.columns.str.strip()

    if 'Data' in df.columns:
        df = df.dropna(subset=['Data'])
        df = df[df['Data'].astype(str).str.contains('/')]

    return df

def processar_extrato(df):
    registros = []

    for _, row in df.iterrows():
        try:
            hist = str(row.iloc[1])
            A = str(row.iloc[3])
            B = str(row.iloc[4])

            if B not in ['nan','0,00','0','']:
                valor = abs(tratar_valor(B))
                tipo = "saída"
            elif A not in ['nan','0,00','0','']:
                valor = tratar_valor(A)
                tipo = "entrada"
            else:
                continue

            registros.append({
                "mes":"ABRIL",
                "descricao":hist,
                "valor":valor,
                "tipo":tipo,
                "status":"pago"
            })
        except:
            continue

    return registros

# --- BACKUP ---
def gerar_backup():
    res = supabase.table("transacoes").select("*").execute()
    if not res.data:
        return None
    return pd.DataFrame(res.data).to_csv(index=False).encode('utf-8')

def tratar_backup(df):
    for c in ['id','criado_em']:
        if c in df.columns:
            df = df.drop(columns=[c])
    return df.to_dict(orient='records')

# --- CLONAR / EXCLUIR MÊS ---
def clonar_mes(origem, destino):
    res = supabase.table("transacoes").select("*").eq("mes", origem).execute()

    if not res.data:
        st.warning("Nada pra copiar")
        return

    novos = [{
        "mes": destino,
        "descricao": i['descricao'],
        "valor": i['valor'],
        "tipo": i['tipo'],
        "status": "pendente"
    } for i in res.data]

    inserir_dados(novos)

def excluir_mes(mes):
    supabase.table("transacoes").delete().eq("mes", mes).execute()
    st.warning(f"{mes} foi limpo")
    st.rerun()

# --- DADOS ---
def carregar_dados(mes):
    if mes == "TODOS":
        res = supabase.table("transacoes").select("*").execute()
    else:
        res = supabase.table("transacoes").select("*").eq("mes", mes).execute()
    return pd.DataFrame(res.data)

def calcular_metricas(df):
    df['valor'] = pd.to_numeric(df['valor'])

    pagos = df[(df['status'].str.lower()=='pago') & (df['tipo'].str.lower().isin(['saida','saída']))]['valor'].sum()
    pend = df[(df['status'].str.lower()=='pendente') & (df['tipo'].str.lower().isin(['saida','saída']))]['valor'].sum()
    ent = df[df['tipo'].str.lower()=='entrada']['valor'].sum()

    return pagos, pend, ent

        # --- SIDEBAR ---

if "limpar_form" not in st.session_state:
    st.session_state.limpar_form = False

def sidebar():
    with st.sidebar:
        st.header("💼 Controle")

        # 🔥 LIMPA ANTES DE RENDERIZAR OS INPUTS
        if st.session_state.limpar_form:
            st.session_state.desc_input = ""
            st.session_state.valor_input = 0.0
            st.session_state.tipo_input = "Saída"
            st.session_state.status_input = "Pendente"
            st.session_state.limpar_form = False

        # INPUTS
        mes = st.selectbox("Mês", MESES, key="mes_input")
        desc = st.text_input("Descrição", key="desc_input")
        valor = st.number_input("Valor", min_value=0.0, key="valor_input")
        tipo = st.radio("Tipo", ["Saída","Entrada"], key="tipo_input")
        status = st.selectbox("Status", ["Pendente","Pago"], key="status_input")

        # BOTÃO SALVAR
        if st.button("Salvar"):
            if st.session_state.desc_input:
                inserir_dados([{
                    "mes": st.session_state.mes_input,
                    "descricao": st.session_state.desc_input,
                    "valor": st.session_state.valor_input,
                    "tipo": st.session_state.tipo_input,
                    "status": st.session_state.status_input
                }])

                # 🔥 sincroniza filtro
                st.session_state.mes_filtro = st.session_state.mes_input

                # 🔥 ativa limpeza
                st.session_state.limpar_form = True

                st.rerun()

        st.divider()

        # IMPORTAR CSV
        arq = st.file_uploader("Importar CSV", type="csv")
        if arq:
            df = ler_extrato(arq)
            st.write(df.head())

            if st.button("Processar CSV"):
                inserir_dados(processar_extrato(df))

        st.divider()

        # RESTAURAR BACKUP
        backup = st.file_uploader("Restaurar Backup", type="csv", key="bkp")
        if backup:
            df = pd.read_csv(backup)
            st.write(df.head())

            if st.button("Restaurar"):
                inserir_dados(tratar_backup(df))

        st.divider()

        # CLONAR
        o = st.selectbox("De:", MESES)
        d = st.selectbox("Para:", MESES)
        if st.button("Clonar Mês"):
            if o != d:
                clonar_mes(o,d)

        st.divider()

        # EXCLUIR MÊS
        m = st.selectbox("Excluir mês", MESES)
        if st.checkbox("Confirmar exclusão"):
            if st.button("Excluir"):
                excluir_mes(m)

        st.divider()

        # BACKUP DOWNLOAD
        csv = gerar_backup()
        if csv:
            st.download_button("📥 Backup", csv, "backup.csv")

# --- DASHBOARD ---

def mostrar_dashboard():
    mes = st.selectbox(
    "📅 Mês",
    ["TODOS"] + MESES,
    key="mes_filtro"
)
    df = carregar_dados(mes)

    if df.empty:
        st.info("Nada ainda")
        return

    pagos, pend, ent = calcular_metricas(df)

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

            # 🔥 ORDENA DO MAIS RECENTE PRO MAIS ANTIGO
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

            if st.button("Pagar", key="btn_pagar"):
                ids = [opcoes[s] for s in sel]
                if ids:
                    supabase.table("transacoes").update({"status":"pago"}).in_("id",ids).execute()
                    st.rerun()

    # EXCLUIR
    with col2:
        with st.expander("🗑️ Excluir Registros"):

            opcoes = {
                f"{r['descricao']} | {formatar_real(r['valor'])} | {r['criado_em']}": r['id']
                for _, r in df.iterrows()
            }

            sel = st.multiselect(
                "Selecionar:",
                list(opcoes.keys()),
                key="multi_excluir_reg"
            )

            if st.button("Apagar", key="btn_apagar"):
                ids = [opcoes[s] for s in sel]
                if ids:
                    supabase.table("transacoes").delete().in_("id",ids).execute()
                    st.rerun()

# --- APP ---
st.set_page_config(page_title="Financeiro Pro", layout="wide")
st.title("💰 Financeiro Pro")

sidebar()
mostrar_dashboard()