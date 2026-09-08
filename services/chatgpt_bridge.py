"""Porta de integração para payloads produzidos pelo ChatGPT.

Este módulo define o ponto de entrada entre uma interpretação externa e o
fluxo oficial de transações do Financeiro Pro. Não realiza chamadas de rede,
não acessa o banco diretamente e não substitui a validação do registrador.
"""

from collections.abc import Mapping

from services.external_transaction_service import registrar_transacao_externa


def receber_payload_chatgpt(dados: Mapping) -> bool:
    """Encaminha um payload do ChatGPT para o registrador oficial.

    O payload ainda será tratado como uma proposta externa. A validação,
    normalização, deduplicação e persistência continuam sob responsabilidade
    do fluxo oficial do Financeiro Pro.
    """
    return registrar_transacao_externa(dados)
