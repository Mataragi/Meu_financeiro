import streamlit as st
import pandas as pd
from services.database import inserir_dados, clonar_mes
from utils.processamento import ler_extrato, processar_extrato
from services.supabase_client import supabase
import pandas as pd

MESES = [
    "JANEIRO","FEVEREIRO","MARÇO","ABRIL","MAIO","JUNHO",
    "JULHO","AGOSTO","SETEMBRO","OUTUBRO","NOVEMBRO","DEZEMBRO"
]

def gerar_backup():
    res = supabase.table("transacoes").select("*").execute()
    if not res.data:
        return None
    import pandas as pd
    return pd.DataFrame(res.data).to_csv(index=False).encode('utf-8')

def tratar_backup(df):
    for c in ['id', 'criado_em']:
        if c in df.columns:
            df = df.drop(columns=[c])
    return df.to_dict(orient='records')

def render_sidebar():

    if "limpar_form" not in st.session_state:
        st.session_state.limpar_form = False

    with st.sidebar:
        st.header("💼 Controle")

        # LIMPA CAMPOS
        if st.session_state.limpar_form:
            st.session_state.desc_input = ""
            st.session_state.valor_input = 0.0
            st.session_state.tipo_input = "Saída"
            st.session_state.status_input = "Pendente"
            st.session_state.limpar_form = False

        mes = st.selectbox("Mês", MESES, key="mes_input")
        desc = st.text_input("Descrição", key="desc_input")
        valor = st.number_input("Valor", min_value=0.0, key="valor_input")
        tipo = st.radio("Tipo", ["Saída","Entrada"], key="tipo_input")
        status = st.selectbox("Status", ["Pendente","Pago"], key="status_input")

        if st.button("Salvar"):
            if desc:
                inserir_dados([{
                    "mes": mes,
                    "descricao": desc,
                    "valor": valor,
                    "tipo": tipo,
                    "status": status
                }])

                # sincroniza mês do dashboard
                st.session_state.mes_filtro = mes

                # ativa limpeza
                st.session_state.limpar_form = True

                st.rerun()

        st.divider()

        # CSV
        arq = st.file_uploader("Importar CSV", type="csv")
        if arq:
            df = ler_extrato(arq)
            st.write(df.head())

            if st.button("Processar CSV"):
                inserir_dados(processar_extrato(df))

        st.divider()

        #UPLOAD BACKUP
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
                
        # CLONAR
        o = st.selectbox("De:", MESES)
        d = st.selectbox("Para:", MESES)

        if st.button("Clonar Mês"):
            if o != d:
                clonar_mes(o, d)

        st.divider()

        # DOWNLOAD BACKUP        
        csv = gerar_backup()
        if csv:
            st.download_button("📥 Backup", csv, "backup.csv")

        st.divider()




       