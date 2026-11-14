"""Contrato compartilhado de status e data efetiva de liquidação."""

from datetime import date, datetime
from typing import Any

from utils.status import STATUS_PAGO, STATUS_PENDENTE, normalizar_status


def normalizar_data_liquidacao(valor: Any) -> str | None:
    """Converte uma data de liquidação para ISO, preservando sua ausência."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.date().isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, str):
        try:
            return date.fromisoformat(valor.strip()).isoformat()
        except ValueError as exc:
            raise ValueError("Data de liquidação inválida.") from exc
    raise ValueError("Data de liquidação inválida.")


def validar_status_liquidacao(status: Any, data_liquidacao: Any) -> str | None:
    """Valida a coerência entre status e liquidação.

    ``Pago`` sem data permanece aceito exclusivamente para os registros
    legados. A futura baixa oficial sempre deverá fornecer a data efetiva.
    """
    status_normalizado = normalizar_status(status)
    if status_normalizado not in {STATUS_PAGO, STATUS_PENDENTE}:
        raise ValueError("Status inválido. Use 'Pago' ou 'Pendente'.")

    data_normalizada = normalizar_data_liquidacao(data_liquidacao)
    if status_normalizado == STATUS_PENDENTE and data_normalizada is not None:
        raise ValueError(
            "Uma transação pendente não pode possuir data de liquidação."
        )
    return data_normalizada


def validar_nova_liquidacao(status: Any, data_liquidacao: Any) -> str | None:
    """Aplica o contrato estrito para gravações novas.

    A ausência de data em um registro ``Pago`` só é tolerada durante a
    leitura do acervo anterior à coluna ``data_liquidacao``. Nenhum caminho
    de criação, edição ou baixa deve produzir esse estado daqui em diante.
    """
    status_normalizado = normalizar_status(status)
    data_normalizada = validar_status_liquidacao(
        status_normalizado,
        data_liquidacao,
    )
    if status_normalizado == STATUS_PAGO and data_normalizada is None:
        raise ValueError(
            "Uma transação paga exige data efetiva de liquidação."
        )
    return data_normalizada


