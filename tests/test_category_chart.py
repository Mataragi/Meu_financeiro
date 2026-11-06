import pandas as pd

from components.mobile_helpers import preparar_dados_grafico_categorias


def test_grafico_soma_valores_por_categoria_e_ignora_receitas():
    df = pd.DataFrame([
        {"categoria": "Mercado", "valor": 100, "tipo": "Despesa"},
        {"categoria": "Mercado", "valor": 50, "tipo": "Despesa"},
        {"categoria": "Transporte", "valor": 40, "tipo": "Despesa"},
        {"categoria": "Salário", "valor": 3000, "tipo": "Receita"},
    ])

    resultado = preparar_dados_grafico_categorias(df)

    assert resultado.to_dict("records") == [
        {"categoria": "Mercado", "valor": 150},
        {"categoria": "Transporte", "valor": 40},
    ]


def test_grafico_trata_categoria_nula_e_valores_invalidos():
    df = pd.DataFrame([
        {"categoria": None, "valor": 25, "tipo": "Despesa"},
        {"categoria": "Mercado", "valor": "inválido", "tipo": "Despesa"},
        {"categoria": "Saúde", "valor": 0, "tipo": "Despesa"},
    ])

    resultado = preparar_dados_grafico_categorias(df)

    assert resultado.to_dict("records") == [
        {"categoria": "Sem categoria", "valor": 25}
    ]


def test_grafico_vazio_quando_nao_ha_despesas():
    df = pd.DataFrame([
        {"categoria": "Salário", "valor": 1000, "tipo": "Receita"}
    ])

    assert preparar_dados_grafico_categorias(df).empty


def test_categorias_antigas_ou_desconhecidas_sao_consolidadas_em_outros():
    df = pd.DataFrame([
        {"categoria": "Cartão Crédito Luiz", "valor": 120, "tipo": "Despesa"},
        {"categoria": "Cartão", "valor": 80, "tipo": "Despesa"},
        {"categoria": "Compras", "valor": 50, "tipo": "Despesa"},
        {"categoria": "Mercado", "valor": 30, "tipo": "Despesa"},
    ])

    resultado = preparar_dados_grafico_categorias(df)

    assert resultado.to_dict("records") == [
        {"categoria": "Outros", "valor": 250},
        {"categoria": "Mercado", "valor": 30},
    ]


def test_categoria_oficial_com_emoji_antigo_e_normalizada():
    df = pd.DataFrame([
        {"categoria": "🍔 Alimentação", "valor": 45, "tipo": "Despesa"},
        {"categoria": "Alimentação", "valor": 55, "tipo": "Despesa"},
    ])

    resultado = preparar_dados_grafico_categorias(df)

    assert resultado.to_dict("records") == [
        {"categoria": "Alimentação", "valor": 100}
    ]
