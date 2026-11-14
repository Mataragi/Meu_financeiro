"""Persistência da única configuração consolidada de disponibilidade."""

from services import database
from services.cache import cache_data, invalidar_cache
from services.financial_service import SaldoInicialDisponibilidade, criar_saldo_inicial


@cache_data(ttl=30)
def carregar_saldo_inicial() -> SaldoInicialDisponibilidade | None:
    """Retorna ``None`` se a configuração ainda não foi criada.

    ``None`` é propositalmente diferente de ``SaldoInicial(..., 0)``: a
    ausência precisa ser tratada pela futura interface como configuração
    pendente, sem inventar um saldo inicial.
    """
    configuracao = database.carregar_configuracao_disponibilidade()
    if configuracao is None:
        return None
    return criar_saldo_inicial(
        configuracao["saldo_inicial"],
        configuracao["data_base"],
    )


def salvar_saldo_inicial(valor, data_base) -> SaldoInicialDisponibilidade:
    """Cria ou atualiza idempotentemente a configuração ``id=1``."""
    saldo_inicial = criar_saldo_inicial(valor, data_base)
    database.salvar_configuracao_disponibilidade(
        {
            "id": 1,
            "saldo_inicial": format(saldo_inicial.valor, ".2f"),
            "data_base": saldo_inicial.data_base.isoformat(),
        }
    )
    invalidar_cache(carregar_saldo_inicial)
    return saldo_inicial
