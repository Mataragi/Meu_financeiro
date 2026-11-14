from types import SimpleNamespace

import pytest

from services import database


class _ConsultaPaginada:
    def __init__(self, registros, limite_api=None):
        self.registros = registros
        self.limite_api = limite_api
        self.intervalos = []

    def select(self, _campos):
        return self

    def order(self, coluna):
        assert coluna == "id"
        return self

    def range(self, inicio, fim):
        self.intervalos.append((inicio, fim))
        self.inicio = inicio
        self.fim = fim
        return self

    def gt(self, coluna, valor):
        assert coluna == "id"
        self.maior_que = valor
        return self

    def execute(self):
        registros = self.registros
        if hasattr(self, "maior_que"):
            registros = [
                registro for registro in registros if registro["id"] > self.maior_que
            ]
        fim = self.fim + 1
        pagina = registros[self.inicio:fim]
        if self.limite_api is not None:
            pagina = pagina[:self.limite_api]
        return SimpleNamespace(data=pagina)


class _SupabasePaginado:
    def __init__(self, registros, limite_api=None):
        self.consulta = _ConsultaPaginada(registros, limite_api)

    def table(self, nome):
        assert nome == "transacoes"
        return self.consulta


def test_historico_completo_pagina_alem_do_limite_padrao_da_api(monkeypatch):
    registros = [{"id": indice, "valor": indice} for indice in range(1, 1202)]
    supabase_falso = _SupabasePaginado(registros)
    monkeypatch.setattr(database, "supabase", supabase_falso)

    resultado = database.carregar_historico_completo(tamanho_pagina=500)

    assert list(resultado["id"]) == list(range(1, 1202))
    assert supabase_falso.consulta.intervalos == [
        (0, 499), (0, 499), (0, 499), (0, 499),
    ]


def test_historico_completo_nao_perde_dados_se_limite_da_api_for_menor_que_pagina(
    monkeypatch,
):
    registros = [{"id": indice} for indice in range(1, 251)]
    supabase_falso = _SupabasePaginado(registros, limite_api=100)
    monkeypatch.setattr(database, "supabase", supabase_falso)

    resultado = database.carregar_historico_completo(tamanho_pagina=500)

    assert list(resultado["id"]) == list(range(1, 251))
    assert supabase_falso.consulta.intervalos == [
        (0, 499), (0, 499), (0, 499), (0, 499),
    ]


@pytest.mark.parametrize("tamanho", [0, -1, True, "500"])
def test_historico_completo_rejeita_tamanho_de_pagina_invalido(tamanho):
    with pytest.raises(ValueError, match="Tamanho de página"):
        database.carregar_historico_completo(tamanho)
