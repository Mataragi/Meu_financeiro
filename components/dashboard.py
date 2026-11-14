from datetime import date

import streamlit as st
import pandas as pd
from services.transaction_service import (
    atualizar_status_multiplos,
    carregar_dados,
    liquidar_fatura_cartao,
    excluir_multiplos_do_mes,
    gerar_backup_transacoes,
)
from components.liquidacao_feedback import executar_liquidacao
from services.financial_service import (
    calcular_posicao_configurada,
    referencia_da_competencia,
)
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

    erro_referencia = None
    try:
        posicao = calcular_posicao_configurada(
            referencia_da_competencia(ano, mes)
        )
    except ValueError as exc:
        posicao = None
        erro_referencia = str(exc)

    c1,c2,c3 = st.columns(3)
    if erro_referencia:
        c1.metric("Saldo disponível", "—")
        c2.metric("Resultado acumulado", "—")
        c3.metric("Saldo projetado", "—")
        st.warning(
            f"Não é possível calcular os indicadores nesta referência: {erro_referencia} "
            "Selecione uma competência igual ou posterior à data-base do saldo inicial."
        )
    elif posicao is None:
        c1.metric("Saldo disponível", "—")
        c2.metric("Resultado acumulado", "—")
        c3.metric("Saldo projetado", "—")
        st.info("Configure o saldo inicial e a data-base para calcular os indicadores.")
    else:
        c1.metric("Saldo disponível", f"R$ {posicao.saldo_disponivel:,.2f}")
        c2.metric("Resultado acumulado", f"R$ {posicao.resultado_acumulado:,.2f}")
        c3.metric("Saldo projetado", f"R$ {posicao.saldo_projetado:,.2f}")

    if df.empty:
        st.info("Nada ainda")
        return

    df['valor'] = pd.to_numeric(df['valor'], errors="coerce")

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

            pend_df = df[df['status'] == STATUS_PENDENTE].copy()
            formas = (
                pend_df["forma_pagamento"].fillna("")
                if "forma_pagamento" in pend_df.columns
                else pd.Series("", index=pend_df.index)
            )
            credito = formas.astype(str).str.strip().str.casefold().isin(
                {"crédito", "credito"}
            )
            tipos = (
                pend_df["tipo"]
                if "tipo" in pend_df.columns
                else pd.Series(TIPO_DESPESA, index=pend_df.index)
            )
            pend_credito = pend_df[credito & (tipos == TIPO_DESPESA)].copy()
            pend_df = pend_df[~credito]
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

            data_liquidacao = st.date_input(
                "Data efetiva do pagamento",
                value=date.today(),
                format="DD/MM/YYYY",
                key="data_liquidacao_dashboard",
            )
            if st.button("Pagar"):
                ids = [opcoes[s] for s in sel]
                if ids:
                    if executar_liquidacao(
                        lambda: atualizar_status_multiplos(
                            ids, STATUS_PAGO, data_liquidacao,
                        ),
                        f"{len(ids)} transação(ões) liquidada(s).",
                    ):
                        st.rerun()

            if not pend_credito.empty and mes == "TODOS":
                st.info("Selecione um mês específico para pagar a fatura de Crédito.")
            elif not pend_credito.empty:
                st.divider()
                st.markdown("**💳 Pagar fatura de Crédito**")
                valores_credito = pd.to_numeric(pend_credito["valor"], errors="coerce")
                quantidade_sem_valor = int(valores_credito.isna().sum())
                pend_credito = pend_credito[valores_credito.notna()].copy()
                pend_credito["valor"] = valores_credito[valores_credito.notna()]
                if quantidade_sem_valor:
                    st.warning(
                        "Não é possível pagar a fatura enquanto houver compra de Crédito "
                        "sem valor informado. Corrija os lançamentos primeiro."
                    )
                if pend_credito.empty:
                    st.info("Não há compras de Crédito com valor para liquidar.")
                elif quantidade_sem_valor:
                    st.metric(
                        "Compras pendentes",
                        len(pend_credito) + quantidade_sem_valor,
                    )
                    st.metric(
                        "Subtotal identificado",
                        f"R$ {float(pend_credito['valor'].sum()):,.2f}",
                    )
                else:
                    total_fatura = float(pend_credito["valor"].sum())
                    st.metric("Compras pendentes", len(pend_credito))
                    st.metric("Total da fatura", f"R$ {total_fatura:,.2f}")
                    data_pagamento_fatura = st.date_input(
                        "Data efetiva do pagamento da fatura",
                        value=date.today(),
                        format="DD/MM/YYYY",
                        key="data_liquidacao_fatura_dashboard",
                    )
                    if st.button("Confirmar pagamento da fatura"):
                        quantidade = len(pend_credito)
                        if executar_liquidacao(
                            lambda: liquidar_fatura_cartao(
                                pend_credito["id"].tolist(),
                                data_pagamento_fatura,
                            ),
                            f"Fatura liquidada: {quantidade} compra(s).",
                        ):
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

 
