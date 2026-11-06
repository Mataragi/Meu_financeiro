import pandas as pd

from components.mobile_helpers import filtrar_categoria, filtrar_forma_pagamento


def test_filtrar_categoria_retorna_apenas_categoria_selecionada():
    df = pd.DataFrame([
        {"descricao": "Mercado no crédito", "categoria": "Mercado", "forma_pagamento": "Crédito"},
        {"descricao": "Almoço no débito", "categoria": "Alimentação", "forma_pagamento": "Débito"},
        {"descricao": "Mercado no pix", "categoria": "Mercado", "forma_pagamento": "PIX"},
    ])

    resultado = filtrar_categoria(df, "Mercado")

    assert resultado["descricao"].tolist() == ["Mercado no crédito", "Mercado no pix"]


def test_filtros_de_categoria_e_credito_podem_ser_combinados():
    df = pd.DataFrame([
        {"descricao": "Mercado crédito", "categoria": "Mercado", "forma_pagamento": "Crédito"},
        {"descricao": "Mercado pix", "categoria": "Mercado", "forma_pagamento": "PIX"},
        {"descricao": "Combustível crédito", "categoria": "Transporte", "forma_pagamento": "Crédito"},
    ])

    resultado = filtrar_forma_pagamento(filtrar_categoria(df, "Mercado"), "Crédito")

    assert resultado["descricao"].tolist() == ["Mercado crédito"]


def test_todas_as_categorias_preserva_dataframe():
    df = pd.DataFrame([{"categoria": "Mercado"}, {"categoria": "Saúde"}])

    resultado = filtrar_categoria(df, "Todas")

    assert resultado.equals(df)


def test_sem_categoria_inclui_valores_nulos_e_rotulo_explicito():
    df = pd.DataFrame([
        {"descricao": "Antigo", "categoria": None},
        {"descricao": "Sem classificação", "categoria": "Sem categoria"},
        {"descricao": "Mercado", "categoria": "Mercado"},
    ])

    resultado = filtrar_categoria(df, "Sem categoria")

    assert resultado["descricao"].tolist() == ["Antigo", "Sem classificação"]
