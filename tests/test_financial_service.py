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


def test_fechamento_de_novembro_e_transportado_automaticamente_para_dezembro():
    saldo_inicial = _saldo_inicial(711.26, date(2026, 11, 14))
    transacoes = _transacoes(
        {"tipo": "Despesa", "status": "Pago", "valor": 38.15, "ano": 2026, "mes": "NOVEMBRO", "data_liquidacao": "2026-11-17"},
        {"tipo": "Saída", "status": "Pago", "valor": 58.90, "ano": 2026, "mes": "NOVEMBRO", "data_liquidacao": "2026-11-18"},
        {"tipo": "Receita", "status": "Pago", "valor": 300, "ano": 2026, "mes": "DEZEMBRO", "data_liquidacao": "2026-12-05"},
        {"tipo": "Despesa", "status": "Pago", "valor": 50, "ano": 2026, "mes": "DEZEMBRO", "data_liquidacao": "2026-12-10"},
        {"tipo": "Despesa", "status": "Pendente", "valor": 400, "ano": 2026, "mes": "DEZEMBRO", "data_liquidacao": None},
    )
    novembro = calcular_posicao_financeira(transacoes, date(2026, 11, 30), saldo_inicial)
    dezembro = calcular_posicao_financeira(transacoes, date(2026, 12, 31), saldo_inicial)

    assert novembro.saldo_abertura_competencia == Decimal("711.26")
    assert novembro.data_inicio_periodo_competencia == date(2026, 11, 14)
    assert novembro.movimentacao_liquidada_competencia == Decimal("-97.05")
    assert novembro.saldo_disponivel == Decimal("614.21")
    assert dezembro.saldo_abertura_competencia == novembro.saldo_disponivel
    assert dezembro.data_inicio_periodo_competencia == date(2026, 12, 1)
    assert dezembro.movimentacao_liquidada_competencia == Decimal("250.00")
    assert dezembro.saldo_fechamento_competencia == Decimal("864.21")
    assert dezembro.saldo_disponivel == Decimal("864.21")
    assert dezembro.saldo_projetado == Decimal("464.21")


def test_receita_recebida_no_mes_anterior_pode_financiar_a_competencia_seguinte():
    saldo_inicial = _saldo_inicial(1000, date(2026, 10, 1))
    transacoes = _transacoes(
        {"tipo": "Receita", "status": "Pago", "valor": 4000, "ano": 2026, "mes": "NOVEMBRO", "data_liquidacao": "2026-10-30"},
        {"tipo": "Despesa", "status": "Pago", "valor": 200, "ano": 2026, "mes": "NOVEMBRO", "data_liquidacao": "2026-11-10"},
    )
    novembro = calcular_posicao_financeira(transacoes, date(2026, 11, 30), saldo_inicial)
    assert novembro.saldo_abertura_competencia == Decimal("5000.00")
    assert novembro.movimentacao_liquidada_competencia == Decimal("-200.00")
    assert novembro.saldo_fechamento_competencia == Decimal("4800.00")
    assert novembro.resultado_acumulado == Decimal("3800.00")


def test_mes_vazio_herda_fechamento_anterior_sem_criar_transacao():
    saldo_inicial = _saldo_inicial(250, date(2026, 1, 1))
    transacoes = _transacoes(
        {"tipo": "Despesa", "status": "Pago", "valor": 75, "ano": 2026, "mes": "JANEIRO", "data_liquidacao": "2026-01-20"},
    )
    janeiro = calcular_posicao_financeira(transacoes, date(2026, 1, 31), saldo_inicial)
    fevereiro = calcular_posicao_financeira(transacoes, date(2026, 2, 28), saldo_inicial)
    assert janeiro.saldo_disponivel == Decimal("175.00")
    assert fevereiro.saldo_abertura_competencia == Decimal("175.00")
    assert fevereiro.movimentacao_liquidada_competencia == Decimal("0.00")
    assert fevereiro.saldo_disponivel == Decimal("175.00")


def test_saldo_negativo_e_transportado_para_o_mes_seguinte():
    saldo_inicial = _saldo_inicial(100, date(2026, 1, 1))
    transacoes = _transacoes(
        {"tipo": "Despesa", "status": "Pago", "valor": 150, "ano": 2026, "mes": "JANEIRO", "data_liquidacao": "2026-01-15"},
        {"tipo": "Receita", "status": "Pago", "valor": 200, "ano": 2026, "mes": "FEVEREIRO", "data_liquidacao": "2026-02-10"},
    )
    janeiro = calcular_posicao_financeira(transacoes, date(2026, 1, 31), saldo_inicial)
    fevereiro = calcular_posicao_financeira(transacoes, date(2026, 2, 28), saldo_inicial)
    assert janeiro.saldo_disponivel == Decimal("-50.00")
    assert fevereiro.saldo_abertura_competencia == Decimal("-50.00")
    assert fevereiro.saldo_disponivel == Decimal("150.00")


def test_edicao_retroativa_recalcula_abertura_dos_meses_posteriores():
    saldo_inicial = _saldo_inicial(1000, date(2026, 1, 1))
    janeiro_original = _transacoes(
        {"tipo": "Despesa", "status": "Pago", "valor": 100, "ano": 2026, "mes": "JANEIRO", "data_liquidacao": "2026-01-15"},
    )
    janeiro_corrigido = _transacoes(
        {"tipo": "Despesa", "status": "Pago", "valor": 250, "ano": 2026, "mes": "JANEIRO", "data_liquidacao": "2026-01-15"},
    )
    fevereiro_original = calcular_posicao_financeira(janeiro_original, date(2026, 2, 28), saldo_inicial)
    fevereiro_corrigido = calcular_posicao_financeira(janeiro_corrigido, date(2026, 2, 28), saldo_inicial)
    assert fevereiro_original.saldo_abertura_competencia == Decimal("900.00")
    assert fevereiro_corrigido.saldo_abertura_competencia == Decimal("750.00")
    assert fevereiro_original.saldo_disponivel - fevereiro_corrigido.saldo_disponivel == Decimal("150.00")


def test_movimentacoes_do_primeiro_dia_pertencem_ao_movimento_do_mes():
    saldo_inicial = _saldo_inicial(500, date(2026, 12, 1))
    transacoes = _transacoes(
        {"tipo": "Receita", "status": "Pago", "valor": 100, "ano": 2026, "mes": "DEZEMBRO", "data_liquidacao": "2026-12-01"},
    )
    dezembro = calcular_posicao_financeira(transacoes, date(2026, 12, 31), saldo_inicial)
    assert dezembro.saldo_abertura_competencia == Decimal("500.00")
    assert dezembro.movimentacao_liquidada_competencia == Decimal("100.00")
    assert dezembro.saldo_disponivel == Decimal("600.00")


def test_transporte_automatico_preserva_saldo_na_virada_do_ano():
    saldo_inicial = _saldo_inicial(2000, date(2026, 12, 1))
    transacoes = _transacoes(
        {"tipo": "Despesa", "status": "Pago", "valor": 300, "ano": 2026, "mes": "DEZEMBRO", "data_liquidacao": "2026-12-31"},
        {"tipo": "Receita", "status": "Pago", "valor": 100, "ano": 2027, "mes": "JANEIRO", "data_liquidacao": "2027-01-02"},
    )
    dezembro = calcular_posicao_financeira(transacoes, date(2026, 12, 31), saldo_inicial)
    janeiro = calcular_posicao_financeira(transacoes, date(2027, 1, 31), saldo_inicial)

    assert dezembro.saldo_disponivel == Decimal("1700.00")
    assert janeiro.saldo_abertura_competencia == Decimal("1700.00")
    assert janeiro.movimentacao_liquidada_competencia == Decimal("100.00")
    assert janeiro.saldo_disponivel == Decimal("1800.00")


def test_fevereiro_bissexto_recebe_abertura_do_fechamento_de_janeiro():
    saldo_inicial = _saldo_inicial(500, date(2028, 1, 1))
    transacoes = _transacoes(
        {"tipo": "Despesa", "status": "Pago", "valor": 125, "ano": 2028, "mes": "JANEIRO", "data_liquidacao": "2028-01-31"},
    )
    janeiro = calcular_posicao_financeira(transacoes, date(2028, 1, 31), saldo_inicial)
    fevereiro = calcular_posicao_financeira(transacoes, date(2028, 2, 29), saldo_inicial)

    assert referencia_da_competencia(2028, "FEVEREIRO") == date(2028, 2, 29)
    assert janeiro.saldo_disponivel == Decimal("375.00")
    assert fevereiro.saldo_abertura_competencia == Decimal("375.00")
    assert fevereiro.saldo_disponivel == Decimal("375.00")

[executed on device: desktop (83b4c1e0-9573-42e8-8b13-e3ed1e247eb4)]