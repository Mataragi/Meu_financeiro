from datetime import date
from decimal import Decimal

from services import disponibilidade_service


def _limpar_cache():
    disponibilidade_service.carregar_saldo_inicial.clear()


def test_configuracao_inexistente_e_distinta_de_saldo_zero(monkeypatch):
    monkeypatch.setattr(
        disponibilidade_service.database,
        "carregar_configuracao_disponibilidade",
        lambda: None,
    )
    _limpar_cache()

    assert disponibilidade_service.carregar_saldo_inicial() is None


def test_saldo_inicial_zero_e_uma_configuracao_valida(monkeypatch):
    monkeypatch.setattr(
        disponibilidade_service.database,
        "carregar_configuracao_disponibilidade",
        lambda: {"id": 1, "saldo_inicial": "0.00", "data_base": "2026-10-01"},
    )
    _limpar_cache()

    resultado = disponibilidade_service.carregar_saldo_inicial()

    assert resultado is not None
    assert resultado.valor == Decimal("0.00")
    assert resultado.data_base == date(2026, 10, 1)


def test_salvar_saldo_inicial_cria_ou_atualiza_idempotentemente(monkeypatch):
    gravacoes = []
    invalidacoes = []
    monkeypatch.setattr(
        disponibilidade_service.database,
        "salvar_configuracao_disponibilidade",
        lambda dados: gravacoes.append(dados) or dados,
    )
    monkeypatch.setattr(
        disponibilidade_service,
        "invalidar_cache",
        lambda funcao: invalidacoes.append(funcao),
    )

    criado = disponibilidade_service.salvar_saldo_inicial("125.5", "2026-10-01")
    atualizado = disponibilidade_service.salvar_saldo_inicial("0", date(2026, 11, 1))

    assert criado.valor == Decimal("125.50")
    assert atualizado.valor == Decimal("0.00")
    assert gravacoes == [
        {"id": 1, "saldo_inicial": "125.50", "data_base": "2026-10-01"},
        {"id": 1, "saldo_inicial": "0.00", "data_base": "2026-11-01"},
    ]
    assert invalidacoes == [
        disponibilidade_service.carregar_saldo_inicial,
        disponibilidade_service.carregar_saldo_inicial,
    ]
