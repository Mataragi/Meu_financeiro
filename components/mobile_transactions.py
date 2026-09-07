import pandas as pd
import streamlit as st

from components.mobile_constants import ANOS, CATEGORIAS, MESES
from components.mobile_helpers import filtrar_status, formatar_data, vencimento_seguro
from services.transaction_service import (
    atualizar_registro,
    duplicar_registro,
    excluir_multiplos,
    inserir_parcelado,
)
from utils.formatacao import formatar_real
from utils.status import STATUS_PAGO, STATUS_PENDENTE


def render_mobile_transaction_form(ano, mes):
    if "show_form" not in st.session_state:
        st.session_state.show_form = False

    if st.button("➕ Nova Transação", use_container_width=True):
        st.session_state.show_form = not st.session_state.show_form

    if not st.session_state.get("show_form", False):
        return

    with st.form("nova_transacao"):
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0)
        categoria = st.selectbox("Categoria", CATEGORIAS)
        tipo = st.selectbox("Tipo", ["Saída", "Entrada"])
        status = st.selectbox("Status", [STATUS_PENDENTE, STATUS_PAGO])
        vencimento = st.number_input(
            "Dia do vencimento", min_value=1, max_value=31, value=10, step=1
        )
        total_parcelas = st.number_input(
            "Quantidade de parcelas", min_value=1, max_value=60, value=1, step=1
        )
        st.caption("Use 1 para compra à vista. Use 2 ou mais para parcelar.")

        salvar = st.form_submit_button("💾 Salvar", use_container_width=True)

        if not salvar:
            return

        if mes in ["Selecione", "TODOS"]:
            st.error("Selecione um mês específico para salvar.")
        elif not desc.strip():
            st.error("Informe uma descrição.")
        elif valor <= 0 and status == STATUS_PAGO:
            st.error("Registro pago precisa ter valor maior que zero.")
        elif categoria == "Selecione":
            st.error("Selecione uma categoria.")
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
            )
            st.success(f"{int(total_parcelas)} registros enviados 🚀")
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
    novo_valor = st.number_input(
        "Valor",
        min_value=0.0,
        value=float(registro.get("valor", 0)),
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
    novo_status = st.selectbox(
        "Status",
        [STATUS_PENDENTE, STATUS_PAGO],
        index=0 if registro.get("status") == STATUS_PENDENTE else 1,
        key=f"edit_status_inline_{registro_id}",
    )
    novo_vencimento = st.number_input(
        "Dia do vencimento",
        min_value=1,
        max_value=31,
        value=vencimento_seguro(registro.get("vencimento")),
        step=1,
        key=f"edit_vencimento_inline_{registro_id}",
    )

    col_salvar, col_cancelar = st.columns(2)
    with col_salvar:
        if st.button(
            "💾 Salvar",
            key=f"salvar_edit_inline_{registro_id}",
            use_container_width=True,
        ):
            if not nova_descricao.strip():
                st.error("Informe uma descrição.")
            elif novo_valor <= 0 and novo_status == STATUS_PAGO:
                st.error("Registro pago precisa ter valor maior que zero.")
            else:
                atualizar_registro(
                    registro_id,
                    {
                        "descricao": nova_descricao.strip(),
                        "valor": novo_valor,
                        "categoria": nova_categoria,
                        "status": novo_status,
                        "vencimento": novo_vencimento,
                    },
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
    col_editar, col_excluir, col_duplicar = st.columns(3)

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
        if st.button(
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


def render_mobile_transaction_list(df_base, mes, status_view):
    st.subheader("Transações")

    if mes == "Selecione" or status_view == "Selecione":
        st.info("Selecione um MÊS e um STATUS para visualizar os registros.")
        return

    busca = st.text_input(
        "🔍 Buscar transação", placeholder="Ex: carro, mercado, claro..."
    ).strip()
    df_lista = filtrar_status(df_base.copy(), status_view)

    if busca:
        df_lista = df_lista[
            df_lista["descricao"].astype(str).str.lower().str.contains(
                busca.lower(), na=False
            )
        ]

    if df_lista.empty:
        st.info("Nenhum registro encontrado para esse filtro.")
        return

    if "categoria" not in df_lista.columns:
        df_lista["categoria"] = "Sem categoria"
    if "vencimento" not in df_lista.columns:
        df_lista["vencimento"] = ""

    for _, row in df_lista.iterrows():
        registro = row.to_dict()
        registro_id = registro.get("id")
        titulo = str(registro.get("descricao", "Sem descrição"))
        valor = formatar_real(float(registro.get("valor", 0)))
        status = str(registro.get("status", ""))
        categoria = str(registro.get("categoria", "Sem categoria"))
        data = formatar_data(registro.get("criado_em", ""))

        transacao = st.expander(
            f"{titulo}  ·  {valor}  ·  {status}",
            key=f"transacao_expander_{registro_id}",
            on_change="rerun",
        )
        with transacao:
            st.caption(f"{categoria}  •  {data}")
            _render_transaction_actions(registro)
