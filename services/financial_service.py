"""Cálculo consolidado dos indicadores financeiros.

Este serviço não conhece Streamlit e não persiste dados. Ele separa caixa
realizado (liquidação), resultado econômico (competência) e projeção das
obrigações ainda abertas na data de referência.
"""

from dataclasses import dataclass
from datetime import date, datetime
from calendar import monthrange
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

import pandas as pd

from utils.status import STATUS_PAGO, normalizar_status
from utils.liquidacao import validar_status_liquidacao
from utils.tipo_transacao import (
    TIPO_DESPESA,
    TIPO_RECEITA,
    normalizar_tipos_dataframe,
)


MESES_ORDEM = (
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
)

_CENTAVOS = Decimal("0.01")
_ZERO = Decimal("0.00")


@dataclass(frozen=True)
class SaldoInicialDisponibilidade:
    """Saldo consolidado existente no início de ``data_base``."""

    valor: Decimal
    data_base: date


@dataclass(frozen=True)
class PosicaoFinanceira:
    """Indicadores independentes e pendências existentes na referência."""

    referencia: date
    saldo_disponivel: Decimal
    resultado_acumulado: Decimal
    saldo_projetado: Decimal
    receitas_previstas: Decimal
    despesas_previstas: Decimal
    pendencias: pd.DataFrame
    pagamentos_legados_sem_data: int
    saldo_abertura_competencia: Decimal
    movimentacao_liquidada_competencia: Decimal
    saldo_fechamento_competencia: Decimal
    data_inicio_periodo_competencia: date
    primeira_competencia_controlada: bool


def criar_saldo_inicial(valor: Any, data_base: Any) -> SaldoInicialDisponibilidade:
    """Normaliza o saldo configurado no início do dia informado."""
    return SaldoInicialDisponibilidade(
        valor=_valor_monetario(valor, campo="saldo inicial"),
        data_base=_normalizar_data(data_base, campo="data-base"),
    )


def calcular_posicao_financeira(
    transacoes: pd.DataFrame | None,
    referencia: Any,
    saldo_inicial: SaldoInicialDisponibilidade,
) -> PosicaoFinanceira:
    """Calcula os três indicadores na data de referência.

    ``data_base`` representa o início do seu dia: uma liquidação ocorrida
    nessa mesma data integra o saldo disponível normalmente.

    Registros históricos pagos que ainda não possuem ``data_liquidacao`` usam
    o mês/ano de competência somente como compatibilidade legada. Registros
    novos devem sempre receber a data efetiva de liquidação.
    """
    if not isinstance(saldo_inicial, SaldoInicialDisponibilidade):
        raise ValueError("saldo_inicial deve ser um SaldoInicialDisponibilidade.")

    data_referencia = _normalizar_data(referencia, campo="data de referência")
    if data_referencia < saldo_inicial.data_base:
        raise ValueError("A data de referência não pode ser anterior à data-base.")

    registros = _normalizar_registros(transacoes)
    inicio_mes = date(data_referencia.year, data_referencia.month, 1)
    # No primeiro mês monitorado, o período começa na data-base; nos
    # meses seguintes, começa no primeiro dia e herda o fechamento anterior.
    inicio_periodo_competencia = max(inicio_mes, saldo_inicial.data_base)
    saldo_abertura_competencia = saldo_inicial.valor
    movimentacao_liquidada_competencia = _ZERO
    disponivel = saldo_inicial.valor
    resultado = _ZERO
    receitas_previstas = _ZERO
    despesas_previstas = _ZERO
    pendencias = []
    pagamentos_legados_sem_data = 0

    for _, registro in registros.iterrows():
        competencia = _competencia(registro["ano"], registro["mes"])
        liquidacao = _data_liquidacao_efetiva(registro, competencia)
        _validar_consistencia_registro(registro, liquidacao)
        if _pagamento_legado_sem_data(registro):
            pagamentos_legados_sem_data += 1

        tipo = registro["tipo"]
        if tipo not in {TIPO_RECEITA, TIPO_DESPESA}:
            # Transferências e classificações históricas desconhecidas não
            # pertencem a receita, despesa, resultado ou projeção agregados.
            continue

        valor = _valor_monetario(registro["valor"], campo="valor")
        if competencia is None:
            # Um registro sem competência confiável não pode afetar os
            # indicadores por competência ou projeção.
            continue

        if competencia <= (data_referencia.year, data_referencia.month):
            resultado += valor if tipo == TIPO_RECEITA else -valor

        if (
            liquidacao is not None
            and saldo_inicial.data_base <= liquidacao <= data_referencia
        ):
            variacao_caixa = valor if tipo == TIPO_RECEITA else -valor
            disponivel += variacao_caixa
            if liquidacao < inicio_periodo_competencia:
                # Caixa liquidado antes do mês atual forma sua abertura.
                saldo_abertura_competencia += variacao_caixa
            else:
                # Só liquidações do período alteram o fechamento do mês.
                movimentacao_liquidada_competencia += variacao_caixa

        pendente_na_referencia = (
            competencia <= (data_referencia.year, data_referencia.month)
            and (liquidacao is None or liquidacao > data_referencia)
        )
        if not pendente_na_referencia:
            continue

        if tipo == TIPO_RECEITA:
            receitas_previstas += valor
        else:
            despesas_previstas += valor

        pendencias.append(
            {
                **registro.to_dict(),
                "competencia_referencia": _formatar_competencia(competencia),
                "data_liquidacao_efetiva": liquidacao,
            }
        )

    saldo_fechamento_competencia = (
        saldo_abertura_competencia + movimentacao_liquidada_competencia
    )
    if saldo_fechamento_competencia != disponivel:
        raise RuntimeError(
            "Inconsistência no transporte do saldo entre competências."
        )

    saldo_projetado = disponivel + receitas_previstas - despesas_previstas
    return PosicaoFinanceira(
        referencia=data_referencia,
        saldo_disponivel=_arredondar(disponivel),
        resultado_acumulado=_arredondar(resultado),
        saldo_projetado=_arredondar(saldo_projetado),
        receitas_previstas=_arredondar(receitas_previstas),
        despesas_previstas=_arredondar(despesas_previstas),
        pendencias=pd.DataFrame(pendencias),
        pagamentos_legados_sem_data=pagamentos_legados_sem_data,
        saldo_abertura_competencia=_arredondar(saldo_abertura_competencia),
        movimentacao_liquidada_competencia=_arredondar(
            movimentacao_liquidada_competencia
        ),
        saldo_fechamento_competencia=_arredondar(saldo_fechamento_competencia),
        data_inicio_periodo_competencia=inicio_periodo_competencia,
        primeira_competencia_controlada=(
            data_referencia.year == saldo_inicial.data_base.year
            and data_referencia.month == saldo_inicial.data_base.month
        ),
    )


def calcular_posicao_consolidada(
    referencia: Any,
    saldo_inicial: SaldoInicialDisponibilidade,
) -> PosicaoFinanceira:
    """Calcula a posição usando o histórico já cacheado de transações.

    A importação é tardia para manter as funções de cálculo puras e fáceis de
    testar sem cliente Supabase ou Streamlit.
    """
    from services.transaction_service import carregar_historico_completo

    return calcular_posicao_financeira(
        carregar_historico_completo(),
        referencia,
        saldo_inicial,
    )


def referencia_da_competencia(ano: Any, mes: Any, hoje: date | None = None) -> date:
    """Retorna o último dia da competência, ou hoje para a visão completa."""
    if mes == "TODOS":
        return hoje or date.today()
    competencia = _competencia(ano, mes)
    if competencia is None:
        raise ValueError("Competência de referência inválida.")
    ano_normalizado, numero_mes = competencia
    return date(ano_normalizado, numero_mes, monthrange(ano_normalizado, numero_mes)[1])


def calcular_posicao_configurada(referencia: Any) -> PosicaoFinanceira | None:
    """Calcula a posição apenas quando existe saldo inicial configurado.

    ``None`` representa configuração ausente, nunca um saldo inicial zero
    inventado. Desktop e mobile consomem esta mesma porta de leitura.
    """
    from services.disponibilidade_service import carregar_saldo_inicial

    saldo_inicial = carregar_saldo_inicial()
    if saldo_inicial is None:
        return None
    return calcular_posicao_consolidada(referencia, saldo_inicial)


def _normalizar_registros(transacoes: pd.DataFrame | None) -> pd.DataFrame:
    colunas = [
        "tipo", "status", "valor", "ano", "mes", "data_liquidacao",
    ]
    if transacoes is None or transacoes.empty:
        return pd.DataFrame(columns=colunas)

    dados = normalizar_tipos_dataframe(transacoes.copy())
    for coluna in colunas:
        if coluna not in dados.columns:
            dados[coluna] = None

    # O pandas converte None/NaT em NaN quando uma coluna mistura datas e
    # valores ausentes. O contrato de liquidação aceita None, não float NaN.
    # Normalizamos aqui para que registros pagos legados continuem legíveis.
    dados["data_liquidacao"] = (
        dados["data_liquidacao"]
        .astype(object)
        .where(dados["data_liquidacao"].notna(), None)
    )
    dados["status"] = dados["status"].map(normalizar_status)
    return dados


def _normalizar_data(valor: Any, campo: str) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        try:
            return date.fromisoformat(valor.strip())
        except ValueError as exc:
            raise ValueError(f"{campo.capitalize()} inválida.") from exc
    raise ValueError(f"{campo.capitalize()} inválida.")


def _valor_monetario(valor: Any, campo: str) -> Decimal:
    if valor is None or pd.isna(valor):
        return _ZERO
    try:
        decimal = Decimal(str(valor)).quantize(_CENTAVOS, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{campo.capitalize()} inválido.") from exc
    if not decimal.is_finite():
        raise ValueError(f"{campo.capitalize()} inválido.")
    return decimal


def _competencia(ano: Any, mes: Any) -> tuple[int, int] | None:
    try:
        ano_normalizado = int(ano)
        mes_normalizado = str(mes).strip().upper()
        numero_mes = MESES_ORDEM.index(mes_normalizado) + 1
    except (TypeError, ValueError):
        return None
    return ano_normalizado, numero_mes


def _data_liquidacao_efetiva(
    registro: pd.Series,
    competencia: tuple[int, int] | None,
) -> date | None:
    valor = registro["data_liquidacao"]
    if valor is not None and not pd.isna(valor):
        return date.fromisoformat(
            validar_status_liquidacao(registro["status"], valor)
        )

    # Compatibilidade para a base legada, cujo único indício de caixa é o
    # status Pago no próprio mês de competência.
    if registro["status"] == STATUS_PAGO and competencia is not None:
        return date(competencia[0], competencia[1], 1)
    return None


def _validar_consistencia_registro(
    registro: pd.Series,
    liquidacao: date | None,
) -> None:
    """Recusa estados silenciosamente ambíguos antes de calcular valores."""
    status = registro["status"]
    validar_status_liquidacao(status, registro["data_liquidacao"])
    if liquidacao is not None and status != STATUS_PAGO:
        raise ValueError(
            "Uma transação pendente não pode possuir data de liquidação."
        )


def _pagamento_legado_sem_data(registro: pd.Series) -> bool:
    valor = registro["data_liquidacao"]
    return (
        registro["status"] == STATUS_PAGO
        and (valor is None or pd.isna(valor))
    )


def _formatar_competencia(competencia: tuple[int, int]) -> str:
    return f"{MESES_ORDEM[competencia[1] - 1].title()}/{competencia[0]}"


def _arredondar(valor: Decimal) -> Decimal:
    return valor.quantize(_CENTAVOS, rounding=ROUND_HALF_UP)

[executed on device: desktop (83b4c1e0-9573-42e8-8b13-e3ed1e247eb4)]