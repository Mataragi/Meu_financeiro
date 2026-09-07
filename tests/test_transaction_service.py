import importlib
import sys
import types

import pytest

from utils.status import STATUS_PAGO, STATUS_PENDENTE, normalizar_status


@pytest.fixture
def transaction_service(monkeypatch):
    repository = types.SimpleNamespace(
        inseridos=[],
        atualizacoes=[],
        baixas=[],
    )
    repository.inserir_dados = lambda dados: repository.inseridos.append(dados)
    repository.atualizar_registro = lambda registro_id, dados: repository.atualizacoes.append(
        (registro_id, dados)
    )
    repository.atualizar_status_registro = lambda registro_id, status: repository.baixas.append(
        (registro_id, status)
    )

    cache = types.ModuleType("services.cache")
    cache.cache_data = lambda **_kwargs: lambda func: func
    cache.invalidar_cache_consultas = lambda: None

    import services

    monkeypatch.setitem(sys.modules, "services.database", repository)
    monkeypatch.setitem(sys.modules, "services.cache", cache)
    monkeypatch.setattr(services, "database", repository, raising=False)
    sys.modules.pop("services.transaction_service", None)

    service = importlib.import_module("services.transaction_service")
    yield service, repository

    sys.modules.pop("services.transaction_service", None)


def test_parcelamento_cria_registros_com_competencia_e_grupo(transaction_service):
    service, repository = transaction_service

    service.inserir_parcelado(
        ano=2026,
        mes="NOVEMBRO",
        descricao="Notebook",
        valor_total=300.0,
        tipo="Saída",
        status=STATUS_PENDENTE,
        categoria="Tecnologia",
        total_parcelas=3,
        vencimento=10,
    )

    parcelas = repository.inseridos[0]

    assert len(parcelas) == 3
    assert [parcela["parcela_atual"] for parcela in parcelas] == [1, 2, 3]
    assert {parcela["total_parcelas"] for parcela in parcelas} == {3}
    assert [parcela["valor"] for parcela in parcelas] == [100.0, 100.0, 100.0]
    assert [parcela["mes"] for parcela in parcelas] == ["NOVEMBRO", "DEZEMBRO", "JANEIRO"]
    assert [parcela["ano"] for parcela in parcelas] == [2026, 2026, 2027]
    assert len({parcela["grupo_parcelamento"] for parcela in parcelas}) == 1
    assert parcelas[0]["grupo_parcelamento"] is not None


def test_competencia_avanca_para_janeiro_do_ano_seguinte(transaction_service):
    service, _ = transaction_service

    assert service.calcular_mes_ano_parcela("NOVEMBRO", 2026, 2) == ("JANEIRO", 2027)


def test_competencia_rejeita_mes_invalido(transaction_service):
    service, _ = transaction_service

    with pytest.raises(ValueError, match="Mês inválido"):
        service.calcular_mes_ano_parcela("MES_INVALIDO", 2026, 1)


def test_duplicar_registro_cria_copia_pendente(transaction_service):
    service, repository = transaction_service

    registro = {
        "id": 10,
        "ano": 2026,
        "mes": "SETEMBRO",
        "descricao": "Mercado",
        "valor": 150.5,
        "tipo": "Saída",
        "status": STATUS_PAGO,
        "categoria": "Mercado",
        "vencimento": 10,
        "parcela_atual": 2,
        "total_parcelas": 3,
        "grupo_parcelamento": "grupo-original",
    }

    novo = service.duplicar_registro(registro, "OUTUBRO", 2026)

    assert novo == {
        "ano": 2026,
        "mes": "OUTUBRO",
        "descricao": "Mercado",
        "valor": 150.5,
        "tipo": "Saída",
        "status": STATUS_PENDENTE,
        "categoria": "Mercado",
        "vencimento": 10,
    }
    assert repository.inseridos == [[novo]]


def test_duplicar_registro_rejeita_mes_invalido(transaction_service):
    service, repository = transaction_service

    with pytest.raises(ValueError, match="Mês inválido"):
        service.duplicar_registro({"descricao": "Teste"}, "INVALIDO", 2026)

    assert repository.inseridos == []


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("pago", STATUS_PAGO),
        ("PAGO", STATUS_PAGO),
        ("pendente", STATUS_PENDENTE),
    ],
)
def test_normaliza_status_legado(valor, esperado):
    assert normalizar_status(valor) == esperado


def test_persistencia_recebe_status_padronizado(transaction_service):
    service, repository = transaction_service

    service.inserir_dados([{"descricao": "Teste", "status": "pago"}])

    assert repository.inseridos == [[{"descricao": "Teste", "status": STATUS_PAGO}]]


def test_baixa_persiste_status_pago(transaction_service):
    service, repository = transaction_service

    service.dar_baixa_registro(42)

    assert repository.baixas == [(42, STATUS_PAGO)]
