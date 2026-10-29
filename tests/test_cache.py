from services.cache import invalidar_cache


class CacheFalso:
    def __init__(self):
        self.limpezas = 0

    def clear(self):
        self.limpezas += 1


def test_invalidar_cache_limpa_apenas_a_funcao_informada():
    cache_transacoes = CacheFalso()
    cache_dividas = CacheFalso()

    invalidar_cache(cache_transacoes)

    assert cache_transacoes.limpezas == 1
    assert cache_dividas.limpezas == 0


def test_invalidar_cache_pode_ser_chamado_novamente():
    cache = CacheFalso()

    invalidar_cache(cache)
    invalidar_cache(cache)

    assert cache.limpezas == 2
