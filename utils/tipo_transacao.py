TIPO_RECEITA = "Receita"
TIPO_DESPESA = "Despesa"

_TIPOS_EQUIVALENTES = {
    "receita": TIPO_RECEITA,
    "entrada": TIPO_RECEITA,
    "despesa": TIPO_DESPESA,
    "saida": TIPO_DESPESA,
    "saída": TIPO_DESPESA,
}


def normalizar_tipo(tipo):
    """Retorna o tipo canônico, aceitando também a nomenclatura histórica."""
    try:
        chave = str(tipo).strip().casefold()
    except (AttributeError, TypeError):
        chave = ""

    normalizado = _TIPOS_EQUIVALENTES.get(chave)
    if normalizado is None:
        raise ValueError("Tipo inválido. Use 'Receita' ou 'Despesa'.")
    return normalizado


def normalizar_tipos_dataframe(df):
    """Normaliza tipos conhecidos sem interromper a leitura histórica."""
    if "tipo" not in df.columns:
        return df

    resultado = df.copy()
    resultado["tipo"] = resultado["tipo"].map(_normalizar_tipo_historico)
    return resultado


def _normalizar_tipo_historico(tipo):
    """Normaliza aliases conhecidos e preserva classificações desconhecidas."""
    try:
        return normalizar_tipo(tipo)
    except ValueError:
        return tipo
