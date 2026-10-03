from components.mobile_constants import CATEGORIAS


def test_categorias_do_mobile_refletem_taxonomia_oficial():
    oficiais = [
        "Moradia",
        "Utilidades",
        "Mercado",
        "Alimentação",
        "Transporte",
        "Saúde",
        "Educação",
        "Família",
        "Lazer & Presentes",
        "Cuidados pessoais",
        "Dívidas",
        "Outros",
        "Sem categoria",
    ]

    assert CATEGORIAS == ["Selecione", *oficiais]
    assert not {"Casa", "Contas", "Lazer", "Cartão Crédito Luiz"}.intersection(CATEGORIAS)
