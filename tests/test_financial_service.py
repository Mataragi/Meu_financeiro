from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from services.financial_service import (
    calcular_posicao_configurada,
    calcular_posicao_consolidada,
    calcular_posicao_financeira,
    criar_saldo_inicial,
    referencia_da_competencia,
)


def _saldo_inicial(valor=1000, data_base=date(2026, 10, 1)):
    return criar_saldo_inicial(valor, data_base)


def _transacoes(*registros):
    return pd.DataFrame(registros)


def test_data_base_representa_inicio_do_dia_e_inclui_liquidacao_no_mesmo_dia():
    posicao = calcular_posicao_financeira(
        _transacoes(
            {
                "tipo": "Receita", "status": "Pago", "valor": 100,
                "ano": 2026, "mes": "OUTUBRO", "data_liquidacao": "2026-10-01",
            },
            {
                "tipo": "Despesa", "status": "Pago", "valor": 40,
                "ano": 2026, "mes": "OUTUBRO", "data_liquidacao": "2026-10-01",
            },
        ),
        date(2026, 10, 1),
        _saldo_inicial(),
    )

    assert posicao.saldo_disponivel == Decimal("1060.00")


def test_referencia_da_competencia_usa_ultimo_dia_do_mes():
    assert referencia_da_competencia(2026, "FEVEREIRO") == date(2026, 2, 28)


def test_posicao_configurada_distingue_ausencia_de_saldo_inicial(monkeypatch):
    from services import disponibilidade_service

    monkeypatch.setattr(disponibilidade_service, "carregar_saldo_inicial", lambda: None)
    assert calcular_posicao_configurada(date(2026, 10, 31)) is None


def test_tres_indicadores_separam_competencia_liquidacao_e_pendencia_antiga():
    transacoes = _transacoes(
        {
            "id": 1, "tipo": "Despesa", "status": "Pago", "valor": 1000,
            "ano": 2026, "mes": "OUTUBRO", "data_liquidacao": "2026-11-10",
        },
    )

    outubro = calcular_posicao_financeira(
        transacoes, date(2026, 10, 31), _saldo_inicial()
    )
    novembro = calcular_posicao_financeira(
        transacoes, date(2026, 11, 30), _saldo_inicial()
    )

    assert outubro.saldo_disponivel == Decimal("1000.00")
    assert outubro.resultado_acumulado == Decimal("-1000.00")
    assert outubro.saldo_projetado == Decimal("0.00")
    assert len(outubro.pendencias) == 1
    assert outubro.pendencias.iloc[0]["competencia_referencia"] == "Outubro/2026"

    assert novembro.saldo_disponivel == Decimal("0.00")
    assert novembro.resultado_acumulado == Decimal("-1000.00")
    assert novembro.saldo_projetado == Decimal("0.00")
    assert novembro.pendencias.empty


def test_saldo_disponivel_positivo_pode_ter_projecao_negativa():
    posicao = calcular_posicao_financeira(
        _transacoes(
            {
                "tipo": "Despesa", "status": "Pendente", "valor": 2000,
                "ano": 2026, "mes": "OUTUBRO", "data_liquidacao": None,
            },
        ),
        date(2026, 10, 31),
        _saldo_inicial(),
    )

    assert posicao.saldo_disponivel == Decimal("1000.00")
    assert posicao.saldo_projetado == Decimal("-1000.00")
    assert posicao.resultado_acumulado == Decimal("-2000.00")


def test_resultado_acumulado_negativo_nao_exige_disponivel_negativo():
    posicao = calcular_posicao_financeira(
        _transacoes(
            {
                "tipo": "Despesa", "status": "Pendente", "valor": 500,
                "ano": 2026, "mes": "OUTUBRO", "data_liquidacao": None,
            },
        ),
        date(2026, 10, 31),
        _saldo_inicial(2000),
    )

    assert posicao.resultado_acumulado == Decimal("-500.00")
    assert posicao.saldo_disponivel == Decimal("2000.00")


def test_receita_pendente_antiga_entra_no_projetado_uma_unica_vez():
    transacoes = _transacoes(
        {
            "tipo": "Receita", "status": "Pendente", "valor": 300,
            "ano": 2026, "mes": "OUTUBRO", "data_liquidacao": None,
        },
    )

    novembro = calcular_posicao_financeira(
        transacoes, date(2026, 11, 30), _saldo_inicial()
    )
    dezembro = calcular_posicao_financeira(
        transacoes, date(2026, 12, 31), _saldo_inicial()
    )

    assert novembro.saldo_projetado == Decimal("1300.00")
    assert dezembro.saldo_projetado == Decimal("1300.00")


def test_transferencia_interna_nao_afeta_os_tres_indicadores_agregados():
    posicao = calcular_posicao_financeira(
        _transacoes(
            {
                "tipo": "Transferência", "status": "Pago", "valor": 500,
                "ano": 2026, "mes": "OUTUBRO", "data_liquidacao": "2026-10-10",
            },
        ),
        date(2026, 10, 31),
        _saldo_inicial(),
    )

    assert posicao.saldo_disponivel == Decimal("1000.00")
    assert posicao.resultado_acumulado == Decimal("0.00")
    assert posicao.saldo_projetado == Decimal("1000.00")


def test_registro_legado_pago_usa_competencia_apenas_como_fallback_de_caixa():
    posicao = calcular_posicao_financeira(
        _transacoes(
            {
                "tipo": "Despesa", "status": "Pago", "valor": 200,
                "ano": 2026, "mes": "OUTUBRO", "data_liquidacao": None,
            },
        ),
        date(2026, 10, 31),
        _saldo_inicial(),
    )

    assert posicao.saldo_disponivel == Decimal("800.00")
    assert posicao.despesas_previstas == Decimal("0.00")


def test_referencia_anterior_a_data_base_e_rejeitada():
    with pytest.raises(ValueError, match="anterior à data-base"):
        calcular_posicao_financeira(
            _transacoes(), date(2026, 9, 30), _saldo_inicial()
        )


def test_pendente_com_data_de_liquidacao_e_rejeitado():
    with pytest.raises(ValueError, match="pendente não pode possuir"):
        calcular_posicao_financeira(
            _transacoes(
                {
                    "tipo": "Despesa", "status": "Pendente", "valor": 100,
                    "ano": 2026, "mes": "OUTUBRO",
                    "data_liquidacao": "2026-10-10",
                },
            ),
            date(2026, 10, 31),
            _saldo_inicial(),
        )


def test_data_de_liquidacao_invalida_e_rejeitada():
    with pytest.raises(ValueError, match="Data de liquidação inválida"):
        calcular_posicao_financeira(
            _transacoes(
                {
                    "tipo": "Despesa", "status": "Pago", "valor": 100,
                    "ano": 2026, "mes": "OUTUBRO",
                    "data_liquidacao": "10/10/2026",
                },
            ),
            date(2026, 10, 31),
            _saldo_inicial(),
        )


def test_pago_legado_sem_data_de_liquidacao_permanece_compativel():
    posicao = calcular_posicao_financeira(
        _transacoes(
            {
                "tipo": "Despesa", "status": "Pago", "valor": 100,
                "ano": 2026, "mes": "OUTUBRO", "data_liquidacao": None,
            },
        ),
        date(2026, 10, 31),
        _saldo_inicial(),
    )

    assert posicao.saldo_disponivel == Decimal("900.00")
    assert posicao.pagamentos_legados_sem_data == 1


def test_posicao_consolidada_usa_historico_paginado(monkeypatch):
    from services import database

    transacoes = _transacoes(
        {
            "tipo": "Receita", "status": "Pago", "valor": 50,
            "ano": 2026, "mes": "OUTUBRO", "data_liquidacao": "2026-10-10",
        },
    )
    monkeypatch.setattr(
        database, "carregar_historico_completo", lambda: transacoes
    )
    monkeypatch.setattr(
        database,
        "carregar_dados",
        lambda *_args, **_kwargs: pytest.fail("Não deve consultar carregar_dados."),
    )

    posicao = calcular_posicao_consolidada(date(2026, 10, 31), _saldo_inicial())

    assert posicao.saldo_disponivel == Decimal("1050.00")


def test_historico_com_datas_e_nulos_mistos_nao_rejeita_nan_do_pandas():
    transacoes = _transacoes(
        {
            "tipo": "Despesa", "status": "Pago", "valor": 100,
            "ano": 2026, "mes": "NOVEMBRO", "data_liquidacao": "2026-11-17",
        },
        {
            "tipo": "Despesa", "status": "Pago", "valor": 50,
            "ano": 2026, "mes": "NOVEMBRO", "data_liquidacao": None,
        },
        {
            "tipo": "Despesa", "status": "Pendente", "valor": 25,
            "ano": 2026, "mes": "NOVEMBRO", "data_liquidacao": None,
        },
    )

    posicao = calcular_posicao_financeira(
        transacoes,
        date(2026, 11, 30),
        _saldo_inicial(711.26, date(2026, 11, 14)),
    )

    assert posicao.saldo_disponivel == Decimal("611.26")
    assert posicao.pagamentos_legados_sem_data == 1
    assert posicao.despesas_previstas == Decimal("25.00")
