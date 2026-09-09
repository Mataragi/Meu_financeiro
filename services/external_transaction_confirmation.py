"""Fluxo de preparação e confirmação de transações externas.

Uma proposta pode ser validada e revisada sem persistência. A gravação só
ocorre quando a confirmação explícita chama o registrador oficial.
"""

from collections.abc import Mapping

from services import external_transaction_service


def preparar_transacao_externa(dados: Mapping) -> dict:
    """Valida uma proposta externa sem gravá-la.

    Retorna o payload normalizado junto da informação de duplicidade.
    """
    payload = external_transaction_service._normalizar_payload(dados)
    duplicada = external_transaction_service._transacao_duplicada(payload)
    return {
        "payload": payload,
        "duplicada": duplicada,
    }


def confirmar_transacao_externa(dados: Mapping) -> bool:
    """Confirma explicitamente uma proposta e registra se ela ainda for válida."""
    return external_transaction_service.registrar_transacao_externa(dados)
