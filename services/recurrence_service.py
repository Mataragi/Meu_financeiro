"""Regras e persistência do contrato de recorrências.

Este módulo não conhece Streamlit e ainda não materializa ocorrências. Ele
prepara a regra, controla seu lifecycle e expõe a identidade necessária para
que a próxima etapa delegue a criação ao transaction_service.
"""

from calendar import monthrange
from collections.abc import Mapping
from datetime import date, datetime, timezone
import math

from services import database, transaction_service
from services.cache import invalidar_cache_consultas
from utils.categoria import CATEGORIAS_OFICIAIS
from utils.forma_pagamento import normalizar_forma_pagamento
from utils.recorrencia import (
    PERIODICIDADE_MENSAL,
    PERIODICIDADES_VALIDAS,
    STATUS_RECORRENCIA_ATIVA,
    STATUS_RECORRENCIA_CANCELADA,
    STATUS_RECORRENCIA_PAUSADA,
    STATUS_RECORRENCIA_VALIDOS,
)
from utils.status import STATUS_PENDENTE
from utils.tipo_transacao import normalizar_tipo


CAMPOS_EDITAVEIS = {
    "descricao",
    "valor",
    "tipo",
    "categoria",
    "forma_pagamento",
    "vencimento",
    "periodicidade",
    "dia_programado",
    "data_inicio",
    "data_fim",
}


def _normalizar_descricao(valor):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError("Descrição da recorrência é obrigatória.")
    return valor.strip()


def _normalizar_valor(valor):
    if valor is None or valor == "":
        return None
    if isinstance(valor, bool):
        raise ValueError("Valor da recorrência inválido.")

    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError("Valor da recorrência inválido.") from exc

    if not math.isfinite(numero) or numero <= 0:
        raise ValueError("O valor deve ser maior que zero ou não informado.")
    return numero


def _normalizar_dia(valor, campo):
    if isinstance(valor, bool) or valor is None:
        raise ValueError(f"{campo} é obrigatório.")

    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{campo} inválido.") from exc

    if not math.isfinite(numero) or not numero.is_integer():
        raise ValueError(f"{campo} inválido.")

    dia = int(numero)
    if not 1 <= dia <= 31:
        raise ValueError(f"{campo} deve estar entre 1 e 31.")
    return dia


def _normalizar_data(valor, campo, obrigatoria=False):
    try:
        normalizada = transaction_service.normalizar_data_transacao(valor)
    except ValueError as exc:
        raise ValueError(f"{campo} inválida.") from exc

    if obrigatoria and normalizada is None:
        raise ValueError(f"{campo} é obrigatória.")
    return normalizada


def _normalizar_periodicidade(valor):
    if valor is None or str(valor).strip() == "":
        return PERIODICIDADE_MENSAL

    periodicidade = str(valor).strip().casefold()
    if periodicidade == PERIODICIDADE_MENSAL.casefold():
        return PERIODICIDADE_MENSAL
    raise ValueError("Periodicidade inválida. Use 'Mensal'.")


def _normalizar_status_recorrencia(valor):
    if valor is None or str(valor).strip() == "":
        return STATUS_RECORRENCIA_ATIVA

    status = str(valor).strip().casefold()
    equivalentes = {
        status.casefold(): status for status in STATUS_RECORRENCIA_VALIDOS
    }
    normalizado = equivalentes.get(status)
    if normalizado is None:
        raise ValueError(
            "Status da recorrência inválido. Use 'Ativa', 'Pausada' ou 'Cancelada'."
        )
    return normalizado


def _normalizar_categoria(valor):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError("Categoria da recorrência é obrigatória.")
    categoria = valor.strip()
    if categoria not in CATEGORIAS_OFICIAIS:
        raise ValueError("Categoria da recorrência inválida.")
    return categoria


def normalizar_dados_recorrencia(dados):
    """Valida e normaliza o contrato persistido de uma recorrência."""
    if not isinstance(dados, Mapping):
        raise ValueError("A recorrência deve ser um objeto.")

    obrigatorios = {
        "descricao",
        "tipo",
        "categoria",
        "forma_pagamento",
        "dia_programado",
        "data_inicio",
    }
    ausentes = obrigatorios - dados.keys()
    if ausentes:
        raise ValueError(
            "Campos obrigatórios ausentes: " + ", ".join(sorted(ausentes)) + "."
        )

    data_inicio = _normalizar_data(dados["data_inicio"], "data_inicio", True)
    data_fim = _normalizar_data(dados.get("data_fim"), "data_fim")
    if data_inicio and data_fim and date.fromisoformat(data_fim) < date.fromisoformat(data_inicio):
        raise ValueError("data_fim não pode ser anterior a data_inicio.")

    vencimento = dados.get("vencimento")
    if vencimento is not None:
        vencimento = _normalizar_dia(vencimento, "vencimento")

    normalizados = {
        "descricao": _normalizar_descricao(dados["descricao"]),
        "valor": _normalizar_valor(dados.get("valor")),
        "tipo": normalizar_tipo(dados["tipo"]),
        "categoria": _normalizar_categoria(dados["categoria"]),
        "forma_pagamento": normalizar_forma_pagamento(dados["forma_pagamento"]),
        "vencimento": vencimento,
        "periodicidade": _normalizar_periodicidade(dados.get("periodicidade")),
        "dia_programado": _normalizar_dia(dados["dia_programado"], "dia_programado"),
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "status_recorrencia": _normalizar_status_recorrencia(
            dados.get("status_recorrencia")
        ),
    }

    return normalizados


def _dados_atualizacao_completos(atual, alteracoes):
    base = {
        campo: atual.get(campo)
        for campo in (
            "descricao",
            "valor",
            "tipo",
            "categoria",
            "forma_pagamento",
            "vencimento",
            "periodicidade",
            "dia_programado",
            "data_inicio",
            "data_fim",
            "status_recorrencia",
        )
    }
    campos_desconhecidos = set(alteracoes) - CAMPOS_EDITAVEIS - {"status_recorrencia"}
    if campos_desconhecidos:
        raise ValueError(
            "Campos não editáveis: " + ", ".join(sorted(campos_desconhecidos)) + "."
        )
    base.update(alteracoes)
    return base


def _obter_recorrencia(id_recorrencia):
    if id_recorrencia is None or isinstance(id_recorrencia, bool):
        raise ValueError("id da recorrência inválido.")
    try:
        id_normalizado = int(id_recorrencia)
    except (TypeError, ValueError) as exc:
        raise ValueError("id da recorrência inválido.") from exc

    recorrencia = database.carregar_recorrencia(id_normalizado)
    if not recorrencia:
        raise ValueError("Recorrência não encontrada.")
    return id_normalizado, recorrencia


def criar_recorrencia(dados):
    normalizados = normalizar_dados_recorrencia(dados)
    recorrencia = database.inserir_recorrencia(normalizados)
    invalidar_cache_consultas()
    return recorrencia or normalizados


def listar_recorrencias():
    return database.carregar_recorrencias()


def editar_recorrencia(id_recorrencia, dados):
    id_normalizado, atual = _obter_recorrencia(id_recorrencia)
    completos = _dados_atualizacao_completos(atual, dados)
    normalizados = normalizar_dados_recorrencia(completos)
    _validar_transicao_status(
        atual.get("status_recorrencia"),
        normalizados["status_recorrencia"],
    )
    normalizados["atualizado_em"] = datetime.now(timezone.utc).isoformat()
    atualizada = database.atualizar_recorrencia(id_normalizado, normalizados)
    invalidar_cache_consultas()
    return atualizada or {"id": id_normalizado, **normalizados}


def _validar_transicao_status(atual, novo):
    atual = _normalizar_status_recorrencia(atual)
    novo = _normalizar_status_recorrencia(novo)

    if atual == STATUS_RECORRENCIA_CANCELADA and novo != STATUS_RECORRENCIA_CANCELADA:
        raise ValueError("Uma recorrência cancelada não pode ser reativada.")
    if atual == STATUS_RECORRENCIA_ATIVA and novo == STATUS_RECORRENCIA_ATIVA:
        return
    if atual == STATUS_RECORRENCIA_PAUSADA and novo in {
        STATUS_RECORRENCIA_PAUSADA,
        STATUS_RECORRENCIA_ATIVA,
        STATUS_RECORRENCIA_CANCELADA,
    }:
        return
    if atual == STATUS_RECORRENCIA_ATIVA and novo in {
        STATUS_RECORRENCIA_PAUSADA,
        STATUS_RECORRENCIA_CANCELADA,
    }:
        return
    raise ValueError("Transição de status da recorrência inválida.")


def alterar_status_recorrencia(id_recorrencia, status_recorrencia):
    id_normalizado, atual = _obter_recorrencia(id_recorrencia)
    novo_status = _normalizar_status_recorrencia(status_recorrencia)
    _validar_transicao_status(atual.get("status_recorrencia"), novo_status)
    dados = {
        "status_recorrencia": novo_status,
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
    }
    atualizada = database.atualizar_recorrencia(id_normalizado, dados)
    invalidar_cache_consultas()
    return atualizada or {"id": id_normalizado, **atual, **dados}


def pausar_recorrencia(id_recorrencia):
    return alterar_status_recorrencia(
        id_recorrencia,
        STATUS_RECORRENCIA_PAUSADA,
    )


def reativar_recorrencia(id_recorrencia):
    return alterar_status_recorrencia(
        id_recorrencia,
        STATUS_RECORRENCIA_ATIVA,
    )


def cancelar_recorrencia(id_recorrencia):
    return alterar_status_recorrencia(
        id_recorrencia,
        STATUS_RECORRENCIA_CANCELADA,
    )


def _normalizar_competencia_ocorrencia(valor):
    if isinstance(valor, str) and len(valor.strip()) == 7:
        valor = valor.strip() + "-01"
    normalizado = _normalizar_data(valor, "competencia_ocorrencia", True)
    periodo = date.fromisoformat(normalizado)
    return date(periodo.year, periodo.month, 1)


def chave_ocorrencia(recorrencia_id, competencia_ocorrencia):
    """Retorna a chave lógica estável de uma ocorrência mensal."""
    if recorrencia_id is None or isinstance(recorrencia_id, bool):
        raise ValueError("recorrencia_id inválido.")
    try:
        id_normalizado = int(recorrencia_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("recorrencia_id inválido.") from exc
    return id_normalizado, _normalizar_competencia_ocorrencia(competencia_ocorrencia)


def _data_programada_no_periodo(recorrencia, periodo):
    ultimo_dia = monthrange(periodo.year, periodo.month)[1]
    dia = min(int(recorrencia["dia_programado"]), ultimo_dia)
    return date(periodo.year, periodo.month, dia)


def _normalizar_competencia_mensal(ano, mes):
    if isinstance(ano, bool):
        raise ValueError("Ano inválido.")
    try:
        ano_normalizado = int(ano)
    except (TypeError, ValueError) as exc:
        raise ValueError("Ano inválido.") from exc

    if isinstance(mes, bool):
        raise ValueError("Mês inválido.")

    if isinstance(mes, int):
        numero_mes = mes
    else:
        mes_normalizado = str(mes).strip().upper()
        try:
            numero_mes = transaction_service.MESES_ORDEM.index(mes_normalizado) + 1
        except ValueError as exc:
            raise ValueError("Mês inválido.") from exc

    try:
        return date(ano_normalizado, numero_mes, 1)
    except (TypeError, ValueError) as exc:
        raise ValueError("Competência mensal inválida.") from exc


def _id_recorrencia(recorrencia):
    if not isinstance(recorrencia, Mapping) or "id" not in recorrencia:
        raise ValueError("Recorrência persistida deve possuir id.")
    id_recorrencia = recorrencia["id"]
    if id_recorrencia is None or isinstance(id_recorrencia, bool):
        raise ValueError("recorrencia_id inválido.")
    try:
        return int(id_recorrencia)
    except (TypeError, ValueError) as exc:
        raise ValueError("recorrencia_id inválido.") from exc


def elegivel_para_competencia(recorrencia, competencia_ocorrencia):
    """Verifica elegibilidade básica sem criar transação.

    A data 29/30/31 é ajustada para o último dia válido do mês. A futura etapa
    de materialização deverá manter este comportamento explicitamente testado.
    """
    if not isinstance(recorrencia, Mapping):
        raise ValueError("Recorrência inválida.")

    status = _normalizar_status_recorrencia(recorrencia.get("status_recorrencia"))
    if status != STATUS_RECORRENCIA_ATIVA:
        return False

    periodicidade = _normalizar_periodicidade(recorrencia.get("periodicidade"))
    if periodicidade not in PERIODICIDADES_VALIDAS:
        return False

    periodo = _normalizar_competencia_ocorrencia(competencia_ocorrencia)
    data_inicio = date.fromisoformat(
        _normalizar_data(recorrencia.get("data_inicio"), "data_inicio", True)
    )
    data_fim_normalizada = _normalizar_data(
        recorrencia.get("data_fim"), "data_fim"
    )
    data_fim = (
        date.fromisoformat(data_fim_normalizada)
        if data_fim_normalizada is not None
        else None
    )
    data_programada = _data_programada_no_periodo(recorrencia, periodo)
    return data_programada >= data_inicio and (
        data_fim is None or data_programada <= data_fim
    )


def materializar_recorrencia(recorrencia, ano, mes):
    """Materializa uma recorrência em uma competência mensal específica."""
    periodo = _normalizar_competencia_mensal(ano, mes)
    recorrencia_id = _id_recorrencia(recorrencia)
    normalizada = normalizar_dados_recorrencia(recorrencia)

    if not elegivel_para_competencia(normalizada, periodo):
        return {
            "elegivel": False,
            "materializada": False,
            "criada": False,
            "existente": False,
            "recorrencia_id": recorrencia_id,
            "competencia_ocorrencia": periodo,
        }

    data_programada = _data_programada_no_periodo(normalizada, periodo)
    forma_pagamento = normalizada["forma_pagamento"]
    if forma_pagamento == "Crédito":
        mes_financeiro, ano_financeiro = (
            transaction_service.calcular_competencia_credito(data_programada)
        )
    else:
        mes_financeiro = transaction_service.MESES_ORDEM[data_programada.month - 1]
        ano_financeiro = data_programada.year

    payload = {
        "recorrencia_id": recorrencia_id,
        "competencia_ocorrencia": periodo,
        "descricao": normalizada["descricao"],
        "valor": normalizada["valor"],
        "tipo": normalizada["tipo"],
        "status": STATUS_PENDENTE,
        "categoria": normalizada["categoria"],
        "forma_pagamento": forma_pagamento,
        "data_transacao": data_programada,
        "vencimento": normalizada["vencimento"],
        "mes": mes_financeiro,
        "ano": ano_financeiro,
    }
    resposta = transaction_service.inserir_ocorrencia_recorrencia(payload)
    dados_resposta = getattr(resposta, "data", None)
    criada = bool(dados_resposta)

    return {
        "elegivel": True,
        "materializada": True,
        "criada": criada,
        "existente": not criada,
        "recorrencia_id": recorrencia_id,
        "competencia_ocorrencia": periodo,
        "payload": payload,
    }


def sincronizar_recorrencias(ano, mes):
    """Materializa as recorrências elegíveis de uma competência mensal."""
    periodo = _normalizar_competencia_mensal(ano, mes)
    hoje = date.today()
    periodo_atual = date(hoje.year, hoje.month, 1)
    if periodo != periodo_atual:
        return {
            "criadas": 0,
            "existentes": 0,
            "nao_elegiveis": 0,
        }

    recorrencias = listar_recorrencias()
    if hasattr(recorrencias, "to_dict"):
        recorrencias = recorrencias.to_dict(orient="records")

    resultado = {
        "criadas": 0,
        "existentes": 0,
        "nao_elegiveis": 0,
    }
    for recorrencia in recorrencias or []:
        data_programada = _data_programada_no_periodo(recorrencia, periodo)
        if data_programada > hoje:
            resultado["nao_elegiveis"] += 1
            continue

        materializacao = materializar_recorrencia(
            recorrencia,
            periodo.year,
            transaction_service.MESES_ORDEM[periodo.month - 1],
        )
        if not materializacao["elegivel"]:
            resultado["nao_elegiveis"] += 1
        elif materializacao["criada"]:
            resultado["criadas"] += 1
        else:
            resultado["existentes"] += 1
    return resultado
