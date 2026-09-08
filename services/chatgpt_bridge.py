"""Porta de integração para payloads produzidos pelo ChatGPT.

Este módulo define o ponto de entrada entre uma interpretação externa e o
fluxo oficial de transações do Financeiro Pro. Não realiza chamadas de rede,
não acessa o banco diretamente e não substitui a validação do registrador.
"""

from collections.abc import Mapping

from services.external_transaction_service import (
    confirmar_transacao_externa,
    preparar_transacao_externa,
)


def receber_payload_chatgpt(dados: Mapping) -> dict:
    """Prepara um payload do ChatGPT sem persistir a transação."""
    return preparar_transacao_externa(dados)


def confirmar_payload_chatgpt(proposta: Mapping) -> bool:
    """Confirma uma proposta do ChatGPT e registra a transação."""
    return confirmar_transacao_externa(proposta)
