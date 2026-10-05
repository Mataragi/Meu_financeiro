from datetime import date
from html import escape

import streamlit as st

from components.mobile_helpers import formatar_data
from services import recurrence_service
from utils.categoria import CATEGORIAS_OFICIAIS
from utils.forma_pagamento import FORMAS_PAGAMENTO
from utils.formatacao import formatar_valor_exibicao
from utils.recorrencia import (
    PERIODICIDADE_MENSAL,
    STATUS_RECORRENCIA_ATIVA,
    STATUS_RECORRENCIA_CANCELADA,
    STATUS_RECORRENCIA_PAUSADA,
    STATUS_RECORRENCIA_VALIDOS,
)
from utils.tipo_transacao import TIPO_DESPESA, TIPO_RECEITA


_STATUS_POR_FILTRO = {
    "Todos": None,
    "Ativas": STATUS_RECORRENCIA_ATIVA,
    "Pausadas": STATUS_RECORRENCIA_PAUSADA,
    "Canceladas": STATUS_RECORRENCIA_CANCELADA,
}

_STATUS_VISUAL = {
    STATUS_RECORRENCIA_ATIVA: "🟢",
    STATUS_RECORRENCIA_PAUSADA: "🟠",
    STATUS_RECORRENCIA_CANCELADA: "🔴",
}

_STATUS_PRIORIDADE = {
    status: prioridade
    for prioridade, status in enumerate(STATUS_RECORRENCIA_VALIDOS)
}


def _recorrencias_para_registros(recorrencias):
    if recorrencias is None:
        return []

    if hasattr(recorrencias, "to_dict"):
        return recorrencias.to_dict(orient="records")

    return [registro for registro in recorrencias if isinstance(registro, dict)]


def _filtrar_recorrencias(registros, status_filtro="Todos", busca=""):
    status_alvo = _STATUS_POR_FILTRO.get(status_filtro)
    texto_busca = str(busca or "").strip().casefold()
    filtrados = []

    for registro in registros:
        if status_alvo is not None and registro.get("status_recorrencia") != status_alvo:
            continue

        if texto_busca:
            texto = " ".join(
                str(registro.get(campo) or "")
                for campo in ("descricao", "categoria")
            ).casefold()
            if texto_busca not in texto:
                continue

        filtrados.append(registro)

    return filtrados


def _dia_para_ordenacao(registro):
    try:
        return int(registro.get("dia_programado"))
    except (TypeError, ValueError):
        return 32


def _ordenar_recorrencias(registros):
    return sorted(
        registros,
        key=lambda registro: (
            _STATUS_PRIORIDADE.get(registro.get("status_recorrencia"), len(STATUS_RECORRENCIA_VALIDOS)),
            _dia_para_ordenacao(registro),
        ),
    )


def _limpar_estado_formulario():
    st.session_state["recurrence_form_open"] = False


def _criar_recorrencia(dados):
    try:
        recurrence_service.criar_recorrencia(dados)
    except ValueError as exc:
        st.error(str(exc))
        return False

    st.success("Recorrência criada ✅")
    _limpar_estado_formulario()
    st.rerun()
    return True


def render_mobile_recurrence_form():
    if "recurrence_form_open" not in st.session_state:
        st.session_state["recurrence_form_open"] = False

    if st.button(
        "🔄 Nova Recorrência",
        key="recurrence_toggle_form",
        use_container_width=True,
    ):
        st.session_state["recurrence_form_open"] = not st.session_state[
            "recurrence_form_open"
        ]

    if not st.session_state.get("recurrence_form_open", False):
        return

    with st.form("recurrence_form"):
        descricao = st.text_input("Descrição")
        valor_nao_informado = st.checkbox("Valor não informado")
        valor = st.number_input(
            "Valor",
            min_value=0.0,
            value=0.0,
            step=0.01,
            disabled=valor_nao_informado,
        )
        tipo = st.selectbox("Tipo", [TIPO_RECEITA, TIPO_DESPESA])
        categoria = st.selectbox("Categoria", CATEGORIAS_OFICIAIS)
        forma_pagamento = st.selectbox("Forma de pagamento", FORMAS_PAGAMENTO)

        possui_vencimento = st.checkbox("Possui vencimento")
        vencimento = (
            st.number_input(
                "Dia do vencimento",
                min_value=1,
                max_value=31,
                value=10,
                step=1,
            )
            if possui_vencimento
            else None
        )

        periodicidade = st.selectbox(
            "Periodicidade",
            [PERIODICIDADE_MENSAL],
            disabled=True,
        )
        dia_programado = st.number_input(
            "Dia programado",
            min_value=1,
            max_value=31,
            value=1,
            step=1,
        )
        st.caption(
            "Dia programado indica quando a ocorrência será gerada. "
            "Dias 29, 30 e 31 usam o último dia válido do mês."
        )

        data_inicio = st.date_input(
            "Data inicial",
            value=date.today(),
            format="DD/MM/YYYY",
        )
        sem_data_fim = st.checkbox("Sem data final", value=True)
        data_fim = (
            None
            if sem_data_fim
            else st.date_input(
                "Data final",
                value=data_inicio,
                format="DD/MM/YYYY",
            )
        )
        st.caption(
            "Vencimento é o dia da obrigação financeira e é independente do dia programado."
        )

        col_criar, col_cancelar = st.columns(2)
        with col_criar:
            salvar = st.form_submit_button("💾 Criar", use_container_width=True)
        with col_cancelar:
            cancelar = st.form_submit_button("Cancelar", use_container_width=True)

    if cancelar:
        _limpar_estado_formulario()
        st.rerun()
        return

    if not salvar:
        return

    if not descricao.strip():
        st.error("Informe uma descrição.")
        return

    if not valor_nao_informado and valor <= 0:
        st.error("O valor deve ser maior que zero ou não informado.")
        return

    _criar_recorrencia(
        {
            "descricao": descricao.strip(),
            "valor": None if valor_nao_informado else valor,
            "tipo": tipo,
            "categoria": categoria,
            "forma_pagamento": forma_pagamento,
            "vencimento": vencimento,
            "periodicidade": periodicidade,
            "dia_programado": dia_programado,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
        }
    )


def _render_recorrencia_card(registro):
    descricao = escape(str(registro.get("descricao") or "Sem descrição"))
    valor = escape(str(formatar_valor_exibicao(registro.get("valor"))))
    status = str(registro.get("status_recorrencia") or "")
    status_visual = _STATUS_VISUAL.get(status, "⚪")
    tipo = escape(str(registro.get("tipo") or ""))
    categoria = escape(str(registro.get("categoria") or ""))
    periodicidade = escape(str(registro.get("periodicidade") or ""))
    dia_programado = escape(str(registro.get("dia_programado") or ""))

    with st.container(border=True):
        st.markdown(f"**{descricao}**")
        st.markdown(f"**{valor}** · {status_visual} {escape(status)}")
        st.caption(
            f"{tipo} · {categoria} · {periodicidade} · Dia {dia_programado}"
        )

        forma_pagamento = registro.get("forma_pagamento") or "Não informado"
        vencimento = registro.get("vencimento")
        detalhes = [f"Pagamento: {forma_pagamento}"]
        if vencimento is not None:
            detalhes.append(f"Vencimento: dia {vencimento}")

        data_inicio = formatar_data(registro.get("data_inicio")) or "não informada"
        data_fim = formatar_data(registro.get("data_fim")) or "sem data final"
        detalhes.append(f"Vigência: {data_inicio} até {data_fim}")
        st.caption(" · ".join(str(detalhe) for detalhe in detalhes))


def render_mobile_recurrence_list():
    st.markdown("### 🔄 Recorrências")

    recorrencias = _recorrencias_para_registros(
        recurrence_service.listar_recorrencias()
    )
    status_filtro = st.selectbox(
        "Filtrar status",
        list(_STATUS_POR_FILTRO),
        key="recurrence_status_filter",
    )
    busca = st.text_input(
        "🔍 Buscar recorrência",
        placeholder="Ex: internet, moradia...",
        key="recurrence_search",
    )

    filtradas = _filtrar_recorrencias(recorrencias, status_filtro, busca)
    ordenadas = _ordenar_recorrencias(filtradas)

    if not ordenadas:
        st.info("Nenhuma recorrência encontrada para esse filtro.")
        return

    for recorrencia in ordenadas:
        _render_recorrencia_card(recorrencia)
