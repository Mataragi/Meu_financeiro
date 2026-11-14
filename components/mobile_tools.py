import pandas as pd
import streamlit as st

from services.transaction_service import (
    gerar_backup_transacoes,
    restaurar_backup_historico,
)


def _tratar_backup(df):
    for coluna in ["id", "criado_em"]:
        if coluna in df.columns:
            df = df.drop(columns=[coluna])
    return df.to_dict(orient="records")


def render_mobile_tools():
    with st.expander("⚙️ Ferramentas"):
        st.subheader("💾 Backup")
        backup = gerar_backup_transacoes()
        if backup:
            st.download_button(
                "📥 Baixar backup",
                backup,
                "backup.csv",
                use_container_width=True,
            )
        else:
            st.info("Nenhum dado disponível para gerar backup.")

        st.divider()
        st.subheader("♻️ Restaurar backup")
        arquivo_backup = st.file_uploader(
            "Upload do backup (.csv)",
            type="csv",
            key="restore_backup_mobile",
        )

        if arquivo_backup:
            df = pd.read_csv(arquivo_backup)
            st.write(df.head())

            if st.button("♻️ Restaurar Backup", use_container_width=True):
                dados = _tratar_backup(df)
                if not dados:
                    st.warning("O backup não contém registros para restaurar.")
                else:
                    try:
                        restaurar_backup_historico(dados)
                    except ValueError as exc:
                        st.error(f"Backup não restaurado: {exc}")
                    else:
                        st.success(f"{len(dados)} registros restaurados 🚀")
                        st.rerun()
