"""Caso de uso para registrar transações recebidas de fontes externas.

Este módulo não conhece Streamlit nem acessa o banco diretamente. A criação
passa sempre pelo transaction_service, que permanece como dono da persistência
e da normalização de status.
"""

import math
from collections.abc import Mapping

from services import transaction_service
from utils.forma_pagamento import normalizar_forma_pagamento
from utils.status import normalizar_status_para_persistencia, STATUS_PENDENTE


MESES_VALIDOS = frozenset(transaction_service.MESES_ORDEM)
TIPOS_VALIDOS = {"ENTRADA": "Entrada", "SAÍDA": "Saída", "SAIDA": "Saída"}
CAMPOS_OBRIGATORIOS = frozenset(
    {
        "descricao",
        "valor",
        "tipo",
        "status",
        "mes",
        "ano",
        "categoria",
        "vencimento",
        "forma_pagamento",
        "data_transacao",
    }
)
CAMPOS_DEDUPLICACAO = (
    "descricao",
    "valor",
    "tipo",
    "status",
    "mes",
    "ano",
    "categoria",
    "vencimento",
    "forma_pagamento",
    "data_transacao",
)


def _texto_obrigatorio(dados, campo):
    valor = dados[campo]
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"Campo obrigatório inválido: {campo}.")
    return valor.strip()


def _normalizar_payload(dados):
    if not isinstance(dados, Mapping):
        raise ValueError("A transação externa deve ser um objeto.")

    ausentes = CAMPOS_OBRIGATORIOS - dados.keys()
    if ausentes:
        raise ValueError(f"Campos obrigatórios ausentes: {', '.join(sorted(ausentes))}.")

    descricao = _texto_obrigatorio(dados, "descricao")
    categoria = _texto_obrigatorio(dados, "categoria")

    try:
        valor = float(dados["valor"])
    except (TypeError, ValueError) as exc:
        raise ValueError("Valor inválido.") from exc
    if not math.isfinite(valor) or valor <= 0:
        raise ValueError("O valor deve ser um número maior que zero.")

    tipo_bruto = _texto_obrigatorio(dados, "tipo").upper()
    tipo = TIPOS_VALIDOS.get(tipo_bruto)
    if tipo is None:
        raise ValueError("Tipo inválido. Use 'Entrada' ou 'Saída'.")

    mes = _texto_obrigatorio(dados, "mes").upper()
    if mes not in MESES_VALIDOS:
        raise ValueError("Mês inválido.")

    ano = dados["ano"]
    if isinstance(ano, bool):
        raise ValueError("Ano inválido.")
    try:
        ano = int(ano)
    except (TypeError, ValueError) as exc:
        raise ValueError("Ano inválido.") from exc
    if ano <= 0 or str(dados["ano"]).strip() != str(ano):
        raise ValueError("Ano inválido.")

    vencimento = dados["vencimento"]
    if isinstance(vencimento, bool):
        raise ValueError("Vencimento inválido.")
    try:
        vencimento = int(vencimento)
    except (TypeError, ValueError) as exc:
        raise ValueError("Vencimento inválido.") from exc
    if not 1 <= vencimento <= 31 or str(dados["vencimento"]).strip() != str(vencimento):
        raise ValueError("Vencimento deve estar entre 1 e 31.")

    forma_pagamento = normalizar_forma_pagamento(dados["forma_pagamento"])
    data_transacao = transaction_service.normalizar_data_transacao(
        dados["data_transacao"]
    )
    status = normalizar_status_para_persistencia(dados["status"])

    if forma_pagamento == "Crédito":
        status = STATUS_PENDENTE

    return {
        **dados,
        "descricao": descricao,
        "valor": valor,
        "tipo": tipo,
        "status": status,
        "mes": mes,
        "ano": ano,
        "categoria": categoria,
        "vencimento": vencimento,
        "forma_pagamento": forma_pagamento,
        "data_transacao": data_transacao,
    }


def _valor_comparavel(valor):
    try:
        return round(float(valor), 2)
    except (TypeError, ValueError):
        return valor


def _chave_deduplicacao(dados):
    chave = []
    for campo in CAMPOS_DEDUPLICACAO:
        valor = dados.get(campo)
        if campo in {"descricao", "categoria"}:
            valor = str(valor).strip()
        elif campo == "valor":
            valor = _valor_comparavel(valor)
        elif campo == "tipo":
            valor = TIPOS_VALIDOS.get(str(valor).strip().upper(), valor)
        elif campo == "mes":
            valor = str(valor).strip().upper()
        elif campo == "status":
            valor = normalizar_status_para_persistencia(valor)
        elif campo == "forma_pagamento":
            valor = normalizar_forma_pagamento(valor) if valor is not None else None
        elif campo == "data_transacao":
            valor = transaction_service.normalizar_data_transacao(valor)
        elif campo in {"ano", "vencimento"}:
            valor = int(valor) if valor is not None else None
        chave.append(valor)
    return tuple(chave)


def _transacao_duplicada(payload):
    registros = transaction_service.carregar_dados(payload["mes"], payload["ano"])
    if hasattr(registros, "to_dict"):
        registros = registros.to_dict(orient="records")

    chave = _chave_deduplicacao(payload)
    for registro in registros:
        if not isinstance(registro, Mapping):
            continue
        try:
            if _chave_deduplicacao(registro) == chave:
                return True
        except (TypeError, ValueError):
            continue
    return False


def preparar_transacao_externa(dados):
    """Valida, normaliza e verifica duplicidade sem persistir a transação."""
    payload = _normalizar_payload(dados)
    return {
        "payload": payload,
        "duplicada": _transacao_duplicada(payload),
    }


def confirmar_transacao_externa(proposta):
    """Confirma uma proposta previamente preparada e persiste com nova validação."""
    if not isinstance(proposta, Mapping) or "payload" not in proposta:
        raise ValueError("Proposta de transação externa inválida.")

    payload = _normalizar_payload(proposta["payload"])

    if _transacao_duplicada(payload):
        return False

    transaction_service.inserir_dados([payload])
    return True


def registrar_transacao_externa(dados):
    """Valida e registra uma transação externa; retorna False se duplicada."""
    proposta = preparar_transacao_externa(dados)

    if proposta["duplicada"]:
        return False

    transaction_service.inserir_dados([proposta["payload"]])
    return True
