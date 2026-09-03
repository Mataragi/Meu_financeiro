from services import database
from services.cache import cache_data, invalidar_cache_consultas
from utils.status import normalizar_status, normalizar_status_para_persistencia


def _normalizar_status_dados(dados):
    if "status" not in dados:
        return dados

    return {
        **dados,
        "status": normalizar_status_para_persistencia(dados["status"]),
    }


def _normalizar_status_dataframe(df):
    if "status" in df.columns:
        df["status"] = df["status"].map(normalizar_status)

    return df


def inserir_divida_informal(dados):
    if dados:
        dados_normalizados = [_normalizar_status_dados(dado) for dado in dados]
        database.inserir_divida_informal(dados_normalizados)
        invalidar_cache_consultas()


@cache_data(ttl=30)
def carregar_dividas_informais():
    return _normalizar_status_dataframe(database.carregar_dividas_informais())


def atualizar_divida_informal(id_divida, dados):
    if id_divida and dados:
        dados_normalizados = _normalizar_status_dados(dados)
        database.atualizar_divida_informal(id_divida, dados_normalizados)
        invalidar_cache_consultas()


def excluir_divida_informal(id_divida):
    if id_divida:
        database.excluir_divida_informal(id_divida)
        invalidar_cache_consultas()
