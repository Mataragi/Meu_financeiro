from datetime import date
from html import escape

import altair as alt
import pandas as pd
import streamlit as st

from components.mobile_constants import (
    ANOS,
    CATEGORIAS,
    CATEGORIA_VIEW,
    FORMA_PAGAMENTO_VIEW,
    MESES,
)
from components.mobile_helpers import (
    filtrar_busca,
    filtrar_categoria,
    filtrar_forma_pagamento,
    filtrar_status,
    preparar_dados_grafico_categorias,
    formatar_data,
    valor_seguro,
    vencimento_seguro,
)
from services.transaction_service import (
    atualizar_registro,
    duplicar_registro,
    excluir_multiplos,
    inserir_parcelado,
    prever_parcelas,
)
from utils.forma_pagamento import FORMAS_PAGAMENTO
from utils.formatacao import formatar_valor_exibicao
from utils.status import STATUS_PAGO, STATUS_PENDENTE
from utils.tipo_transacao import TIPO_DESPESA, TIPO_RECEITA


FORMAS_PAGAMENTO_NOVO = list(FORMAS_PAGAMENTO)
FORMAS_PAGAMENTO_EDICAO = ["Não informado", *FORMAS_PAGAMENTO_NOVO]

ICONS_BY_CATEGORY = {
    "Moradia": "🏠",
    "Utilidades": "💡",
    "Mercado": "🛒",
    "Alimentação": "🍽️",
    "Transporte": "🚗",
    "Saúde": "🩺",
    "Educação": "📚",
    "Família": "👨‍👩‍👧",
    "Lazer & Presentes": "🎁",
    "Cuidados pessoais": "✨",
    "Dívidas": "🧾",
    "Outros": "📌",
    "Sem categoria": "📁",
}


def _forma_pagamento_para_exibicao(valor):
    if valor is None:
        return "Não informado"

    try:
        if pd.isna(valor):
            return "Não informado"
    except (TypeError, ValueError):
        pass

    return str(valor)


def _render_transaction_summary(registro):
    categoria = str(registro.get("categoria") or "Sem categoria")
    descricao = str(registro.get("descricao") or "Sem descrição")
    data = formatar_data(registro.get("data_transacao")) or "Data não informada"
    forma_pagamento = _forma_pagamento_para_exibicao(
        registro.get("forma_pagamento")
    )
    status = str(registro.get("status") or "Pendente")
    tipo = str(registro.get("tipo") or TIPO_DESPESA)
    valor = formatar_valor_exibicao(registro.get("valor"))
    status_class = (
        "financeiro-pro-status-pago"
        if status == STATUS_PAGO
        else "financeiro-pro-status-pendente"
    )
    value_class = (
        "financeiro-pro-value-receita"
        if tipo == TIPO_RECEITA
        else "financeiro-pro-value-despesa"
    )
    value_prefix = "+ " if tipo == TIPO_RECEITA else "− "
    icon = ICONS_BY_CATEGORY.get(categoria, "📌")
    recorrencia_id = registro.get("recorrencia_id")
    marcador_recorrencia = ""
    if recorrencia_id is not None:
        try:
            if not pd.isna(recorrencia_id):
                marcador_recorrencia = " · 🔁 Recorrência"
        except (TypeError, ValueError):
            marcador_recorrencia = " · 🔁 Recorrência"
    parcela_atual = registro.get("parcela_atual")
    total_parcelas = registro.get("total_parcelas")
    parcela = ""
    try:
        if (
            parcela_atual is not None
            and total_parcelas is not None
            and not pd.isna(parcela_atual)
            and not pd.isna(total_parcelas)
        ):
            parcela = f" · {int(parcela_atual)}/{int(total_parcelas)}x"
    except (TypeError, ValueError, OverflowError):
        parcela = ""

    st.markdown(
        f"""
        <div class="financeiro-pro-transaction-detail">
            <div class="financeiro-pro-transaction-icon">{icon}</div>
            <div class="financeiro-pro-transaction-main">
                <div class="financeiro-pro-transaction-description">{escape(descricao)}</div>
                <div class="financeiro-pro-transaction-meta">
                    {escape(categoria)}{escape(parcela)} · {escape(data)} · {escape(forma_pagamento)}{escape(marcador_recorrencia)}
                </div>
            </div>
            <div class="financeiro-pro-transaction-side">
                <span class="financeiro-pro-status {status_class}">{escape(status)}</span>
                <span class="financeiro-pro-transaction-value {value_class}">
                    {value_prefix}{escape(valor)}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _data_transacao_para_formulario(registro):
    valor = registro.get("data_transacao")
    if not valor:
        return None

    try:
        return date.fromisoformat(str(valor))
    except ValueError:
        return None


def _render_preview_parcelas(previsao):
    """Renderiza uma prévia compacta e rolável das parcelas calculadas pelo serviço."""
    linhas = []
    for parcela in previsao:
        competencia = f"{parcela['mes'].title()}/{parcela['ano']}"
        valor = formatar_valor_exibicao(parcela["valor"])
        linhas.append(
            "<tr>"
            f"<td>Parcela {parcela['parcela_atual']}/{parcela['total_parcelas']}</td>"
            f"<td>{escape(competencia)}</td>"
            f"<td class='valor'>{escape(valor)}</td>"
            "</tr>"
        )

    html = (
        "<style>"
        ".fp-preview-table{width:100%;border-collapse:collapse;font-size:.82rem;}"
        ".fp-preview-table td{padding:.38rem .45rem;border-bottom:1px solid rgba(128,128,128,.18);}"
        ".fp-preview-table tr:last-child td{border-bottom:0;}"
        ".fp-preview-table .valor{text-align:right;font-weight:650;white-space:nowrap;}"
        "</style>"
        "<table class='fp-preview-table'><tbody>"
        + "".join(linhas)
        + "</tbody></table>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_mobile_transaction_form(ano, mes):
    if "show_form" not in st.session_state:
        st.session_state.show_form = False

    if st.button(
        "➕ Nova Transação",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.show_form = not st.session_state.show_form

    if not st.session_state.get("show_form", False):
        return

    with st.container(border=True):
        st.markdown("### Nova transação")
        st.caption("Registre uma movimentação financeira.")

        desc = st.text_input(
            "Descrição",
            placeholder="Ex.: Compra no mercado",
            key="nova_desc",
        )

        col_valor, col_tipo = st.columns(2, gap="small")
        with col_valor:
            valor = st.number_input(
                "Valor (R$)",
                min_value=0.0,
                value=0.0,
                step=0.01,
                format="%.2f",
                key="nova_valor",
            )
        with col_tipo:
            tipo = st.selectbox(
                "Tipo",
                [TIPO_DESPESA, TIPO_RECEITA],
                key="nova_tipo",
            )

        col_categoria, col_pagamento, col_status = st.columns(3, gap="small")
        with col_categoria:
            categoria = st.selectbox(
                "Categoria",
                CATEGORIAS,
                key="nova_categoria",
            )
        with col_pagamento:
            forma_pagamento = st.selectbox(
                "Forma de pagamento",
                FORMAS_PAGAMENTO_NOVO,
                key="nova_forma_pagamento",
            )
        with col_status:
            if forma_pagamento == "Crédito":
                status = STATUS_PENDENTE
                st.selectbox(
                    "Status",
                    [STATUS_PENDENTE],
                    disabled=True,
                    key="nova_status_credito",
                    help="Compras no crédito entram como pendentes até a baixa da fatura.",
                )
            else:
                status = st.selectbox(
                    "Status",
                    [STATUS_PENDENTE, STATUS_PAGO],
                    key="nova_status",
                )

        st.markdown("**Datas**")
        col_data, col_vencimento = st.columns([1.35, 1], gap="small")
        with col_data:
            data_transacao = st.date_input(
                "Data da transação",
                value=date.today(),
                format="DD/MM/YYYY",
                key="nova_data_transacao",
            )
        with col_vencimento:
            possui_vencimento = st.checkbox(
                "Possui vencimento",
                value=False,
                key="nova_possui_vencimento",
            )
            if possui_vencimento:
                dia_vencimento = st.number_input(
                    "Dia do vencimento",
                    min_value=1,
                    max_value=31,
                    value=10,
                    step=1,
                    key="nova_dia_vencimento",
                )
                vencimento = int(dia_vencimento)
            else:
                vencimento = None

        st.markdown("**Parcelamento**")
        col_parcelas, col_info = st.columns([1, 2], gap="small")
        with col_parcelas:
            total_parcelas = st.number_input(
                "Quantidade de parcelas",
                min_value=1,
                max_value=60,
                value=1,
                step=1,
                key="nova_total_parcelas",
            )
        with col_info:
            st.caption("De 1 a 60 parcelas. A prévia não grava dados.")

        previsao = []
        erro_previa = None
        if valor > 0 and int(total_parcelas) > 1 and mes not in ["Selecione", "TODOS"]:
            try:
                previsao = prever_parcelas(
                    ano=ano,
                    mes=mes,
                    valor_total=valor,
                    total_parcelas=int(total_parcelas),
                    forma_pagamento=forma_pagamento,
                    data_transacao=data_transacao,
                )
            except ValueError as exc:
                erro_previa = str(exc)

        if int(total_parcelas) > 1:
            if erro_previa:
                st.warning(erro_previa)
            elif previsao:
                st.markdown("**Prévia das parcelas**")
                with st.container(height=220, border=True):
                    _render_preview_parcelas(previsao)
                total_previsto = round(sum(item["valor"] for item in previsao), 2)
                st.caption(
                    f"Total: {formatar_valor_exibicao(total_previsto)} · "
                    f"{previsao[0]['mes'].title()}/{previsao[0]['ano']} até "
                    f"{previsao[-1]['mes'].title()}/{previsao[-1]['ano']}"
                )

        if forma_pagamento == "Crédito":
            st.caption(
                "A competência do crédito é calculada pela data da transação, "
                "conforme a regra atual de fechamento."
            )

        salvar = st.button(
            "💾 Salvar transação",
            type="primary",
            use_container_width=True,
            key="salvar_nova_transacao",
        )

        if salvar:
            if mes in ["Selecione", "TODOS"]:
                st.error("Selecione um mês específico para salvar.")
            elif not desc.strip():
                st.error("Informe uma descrição.")
            elif valor <= 0:
                st.error("O valor deve ser maior que zero.")
            elif categoria == "Selecione":
                st.error("Selecione uma categoria.")
            elif erro_previa:
                st.error(erro_previa)
            else:
                inserir_parcelado(
                    ano=ano,
                    mes=mes,
                    descricao=desc.strip(),
                    valor_total=valor,
                    tipo=tipo,
                    status=status,
                    categoria=categoria,
                    total_parcelas=int(total_parcelas),
                    vencimento=vencimento,
                    forma_pagamento=forma_pagamento,
                    data_transacao=data_transacao,
                )
                st.success(f"{int(total_parcelas)} registro(s) enviado(s) 🚀")
                st.session_state.show_form = False
                st.rerun()


def _limpar_estado_registro(registro_id):
    for prefixo in [
        "editando_transacao",
        "confirmar_exclusao",
        "duplicando_transacao",
    ]:
        st.session_state.pop(f"{prefixo}_{registro_id}", None)


def _render_edicao_inline(registro):
    registro_id = registro.get("id")
    nova_descricao = st.text_input(
        "Descrição",
        value=str(registro.get("descricao", "")),
        key=f"edit_desc_inline_{registro_id}",
    )
    valor_atual = valor_seguro(registro.get("valor"))
    novo_valor = st.number_input(
        "Valor",
        min_value=0.0,
        value=valor_atual,
        key=f"edit_valor_inline_{registro_id}",
    )
    categoria_atual = registro.get("categoria", "Sem categoria")
    nova_categoria = st.selectbox(
        "Categoria",
        CATEGORIAS,
        index=CATEGORIAS.index(categoria_atual)
        if categoria_atual in CATEGORIAS
        else 1,
        key=f"edit_categoria_inline_{registro_id}",
    )

    forma_atual = registro.get("forma_pagamento")
    forma_index = (
        FORMAS_PAGAMENTO_EDICAO.index(forma_atual)
        if forma_atual in FORMAS_PAGAMENTO_EDICAO
        else 0
    )
    nova_forma_pagamento = st.selectbox(
        "Forma de pagamento",
        FORMAS_PAGAMENTO_EDICAO,
        index=forma_index,
        key=f"edit_forma_pagamento_inline_{registro_id}",
    )

    novo_status = st.selectbox(
        "Status",
        [STATUS_PENDENTE, STATUS_PAGO],
        index=0 if registro.get("status") == STATUS_PENDENTE else 1,
        key=f"edit_status_inline_{registro_id}",
    )
    if valor_atual is None:
        st.info("Valor não informado. Preencha o valor; a ocorrência continuará pendente.")
        novo_status = STATUS_PENDENTE
    possui_vencimento = st.checkbox(
        "Possui vencimento",
        value=registro.get("vencimento") is not None,
        key=f"possui_vencimento_inline_{registro_id}",
    )
    novo_vencimento = (
        st.number_input(
            "Dia do vencimento",
            min_value=1,
            max_value=31,
            value=vencimento_seguro(registro.get("vencimento")),
            step=1,
            key=f"edit_vencimento_inline_{registro_id}",
        )
        if possui_vencimento
        else None
    )

    data_existente = _data_transacao_para_formulario(registro)
    if data_existente is not None:
        nova_data_transacao = st.date_input(
            "Data da transação",
            value=data_existente,
            format="DD/MM/YYYY",
            key=f"edit_data_transacao_inline_{registro_id}",
        )
    else:
        nova_data_transacao = None
        st.caption("Data da transação não informada neste registro histórico.")

    if nova_forma_pagamento == "Crédito" and registro.get("forma_pagamento") != "Crédito":
        st.info("Ao alterar para Crédito, o status será salvo como Pendente.")
        novo_status = STATUS_PENDENTE

    col_salvar, col_cancelar = st.columns(2)
    with col_salvar:
        if st.button(
            "💾 Salvar",
            key=f"salvar_edit_inline_{registro_id}",
            use_container_width=True,
        ):
            if not nova_descricao.strip():
                st.error("Informe uma descrição.")
            elif novo_valor is None and valor_atual is not None:
                st.error("Informe um valor maior que zero.")
            elif novo_valor is not None and novo_valor <= 0:
                st.error("O valor deve ser maior que zero.")
            else:
                dados_atualizacao = {
                    "descricao": nova_descricao.strip(),
                    "valor": novo_valor,
                    "categoria": nova_categoria,
                    "status": novo_status,
                    "vencimento": novo_vencimento,
                }
                if nova_forma_pagamento == "Não informado":
                    dados_atualizacao["forma_pagamento"] = None
                else:
                    dados_atualizacao["forma_pagamento"] = nova_forma_pagamento
                if nova_data_transacao is not None:
                    dados_atualizacao["data_transacao"] = nova_data_transacao

                atualizar_registro(
                    registro_id,
                    dados_atualizacao,
                )
                st.success("Registro atualizado ✅")
                _limpar_estado_registro(registro_id)
                st.rerun()

    with col_cancelar:
        if st.button(
            "Cancelar",
            key=f"cancelar_edit_inline_{registro_id}",
            use_container_width=True,
        ):
            _limpar_estado_registro(registro_id)
            st.rerun()


def _render_duplicacao_inline(registro):
    registro_id = registro.get("id")
    meses_destino = MESES[2:]
    ano_origem = int(registro.get("ano", ANOS[0]))
    mes_origem = str(registro.get("mes", meses_destino[0]))
    ano_index = ANOS.index(ano_origem) if ano_origem in ANOS else 0
    mes_index = meses_destino.index(mes_origem) if mes_origem in meses_destino else 0

    st.caption("A cópia será criada como Pendente.")
    col_mes, col_ano = st.columns(2)
    with col_mes:
        mes_destino = st.selectbox(
            "Mês de destino",
            meses_destino,
            index=mes_index,
            key=f"dup_mes_{registro_id}",
        )
    with col_ano:
        ano_destino = st.selectbox(
            "Ano de destino",
            ANOS,
            index=ano_index,
            key=f"dup_ano_{registro_id}",
        )

    col_confirmar, col_cancelar = st.columns(2)
    with col_confirmar:
        if st.button(
            "📋 Criar cópia",
            key=f"confirmar_dup_{registro_id}",
            use_container_width=True,
        ):
            duplicar_registro(registro, mes_destino, ano_destino)
            st.success("Cópia criada como pendente ✅")
            _limpar_estado_registro(registro_id)
            st.rerun()
    with col_cancelar:
        if st.button(
            "Cancelar",
            key=f"cancelar_dup_{registro_id}",
            use_container_width=True,
        ):
            _limpar_estado_registro(registro_id)
            st.rerun()


def _render_transaction_actions(registro):
    registro_id = registro.get("id")
    st.markdown(
        '<div class="financeiro-pro-action-label">Ações</div>',
        unsafe_allow_html=True,
    )
    col_editar, col_excluir, col_duplicar = st.columns(3, gap="small")

    with col_editar:
        if st.button(
            "✏️ Editar",
            key=f"editar_transacao_{registro_id}",
            use_container_width=True,
        ):
            st.session_state[f"editando_transacao_{registro_id}"] = True
            st.session_state[f"confirmar_exclusao_{registro_id}"] = False
            st.session_state[f"duplicando_transacao_{registro_id}"] = False

    with col_excluir:
        recorrencia_id = registro.get("recorrencia_id")
        eh_recorrencia = recorrencia_id is not None
        try:
            eh_recorrencia = eh_recorrencia and not pd.isna(recorrencia_id)
        except (TypeError, ValueError):
            pass
        if eh_recorrencia:
            st.button(
                "🗑️ Excluir",
                key=f"excluir_transacao_{registro_id}",
                use_container_width=True,
                disabled=True,
                help="Preserve a ocorrência vinculada à regra de recorrência.",
            )
        elif st.button(
            "🗑️ Excluir",
            key=f"excluir_transacao_{registro_id}",
            use_container_width=True,
        ):
            st.session_state[f"confirmar_exclusao_{registro_id}"] = True
            st.session_state[f"editando_transacao_{registro_id}"] = False
            st.session_state[f"duplicando_transacao_{registro_id}"] = False

    with col_duplicar:
        if st.button(
            "📋 Duplicar",
            key=f"duplicar_transacao_{registro_id}",
            type="secondary",
            use_container_width=True,
        ):
            st.session_state[f"duplicando_transacao_{registro_id}"] = True
            st.session_state[f"editando_transacao_{registro_id}"] = False
            st.session_state[f"confirmar_exclusao_{registro_id}"] = False

    if st.session_state.get(f"confirmar_exclusao_{registro_id}"):
        st.warning("Tem certeza que deseja excluir este registro?")
        col_confirmar, col_cancelar = st.columns(2)
        with col_confirmar:
            if st.button(
                "Confirmar exclusão",
                key=f"confirmar_exclusao_btn_{registro_id}",
                type="primary",
                use_container_width=True,
            ):
                excluir_multiplos([registro_id])
                st.success("Registro excluído.")
                _limpar_estado_registro(registro_id)
                st.rerun()
        with col_cancelar:
            if st.button(
                "Cancelar",
                key=f"cancelar_exclusao_btn_{registro_id}",
                use_container_width=True,
            ):
                _limpar_estado_registro(registro_id)
                st.rerun()

    if st.session_state.get(f"editando_transacao_{registro_id}"):
        st.divider()
        _render_edicao_inline(registro)

    if st.session_state.get(f"duplicando_transacao_{registro_id}"):
        st.divider()
        _render_duplicacao_inline(registro)


def _render_category_expense_chart(df_lista, categoria_view):
    dados_grafico = preparar_dados_grafico_categorias(df_lista)
    if dados_grafico.empty:
        st.info("Não há despesas com valores para compor o gráfico.")
        return

    total = dados_grafico["valor"].sum()
    titulo = (
        f"Despesas por categoria · {categoria_view}"
        if categoria_view != "Todas"
        else "Distribuição das despesas por categoria"
    )
    st.markdown(f"**{titulo}**")
    st.metric("Total de despesas no filtro", formatar_valor_exibicao(total))

    altura = max(240, min(560, len(dados_grafico) * 30))
    grafico = (
        alt.Chart(dados_grafico)
        .mark_bar(cornerRadiusEnd=5, height=18)
        .encode(
            x=alt.X(
                "valor:Q",
                title="Valor gasto",
                axis=alt.Axis(format="$,.0f", grid=True),
            ),
            y=alt.Y(
                "categoria:N",
                title=None,
                sort="-x",
                axis=alt.Axis(labelLimit=150),
            ),
            color=alt.Color(
                "categoria:N",
                legend=None,
                scale=alt.Scale(scheme="tableau20"),
            ),
            tooltip=[
                alt.Tooltip("categoria:N", title="Categoria"),
                alt.Tooltip("valor:Q", title="Total", format="$,.2f"),
            ],
        )
        .properties(height=altura)
    )
    st.altair_chart(grafico, use_container_width=True)


def render_mobile_transaction_list(
    df_base,
    mes,
    status_view="Todos",
    forma_pagamento_view=None,
):
    st.markdown(
        '<div class="financeiro-pro-transactions-title">Transações</div>',
        unsafe_allow_html=True,
    )

    col_categoria, col_pagamento = st.columns(2, gap="small")
    with col_categoria:
        categoria_view = st.selectbox(
            "Categoria",
            CATEGORIA_VIEW,
            key="categoria_view_mobile",
        )

    with col_pagamento:
        forma_pagamento_view = st.selectbox(
            "Forma de pagamento",
            FORMA_PAGAMENTO_VIEW,
            key="forma_pagamento_view_mobile",
        )

    busca = st.text_input(
        "🔍 Buscar transação",
        placeholder="Ex: carro, mercado...",
        key="busca_transacao_mobile",
    ).strip()

    if mes == "Selecione":
        st.info("Selecione um MÊS para visualizar os registros.")
        return

    df_lista = filtrar_status(df_base.copy(), status_view)
    df_lista = filtrar_categoria(df_lista, categoria_view)
    df_lista = filtrar_forma_pagamento(df_lista, forma_pagamento_view)

    if busca:
        df_lista = filtrar_busca(df_lista, busca)

    if df_lista.empty:
        st.info("Nenhum registro encontrado para esse filtro.")
        return

    _render_category_expense_chart(df_lista, categoria_view)

    if "categoria" not in df_lista.columns:
        df_lista["categoria"] = "Sem categoria"
    if "vencimento" not in df_lista.columns:
        df_lista["vencimento"] = ""

    for _, row in df_lista.iterrows():
        registro = row.to_dict()
        registro_id = registro.get("id")
        titulo = str(registro.get("descricao", "Sem descrição"))
        valor = formatar_valor_exibicao(registro.get("valor"))
        status = str(registro.get("status", ""))
        tipo = str(registro.get("tipo") or TIPO_DESPESA)
        icon = ICONS_BY_CATEGORY.get(
            str(registro.get("categoria") or "Sem categoria"),
            "📌",
        )
        valor_prefixo = "+ " if tipo == TIPO_RECEITA else "− "

        transacao = st.expander(
            f"{icon}  {titulo}  ·  {valor_prefixo}{valor}  ·  {status}",
            key=f"transacao_expander_{registro_id}",
            on_change="rerun",
        )
        with transacao:
            _render_transaction_summary(registro)
            _render_transaction_actions(registro)
