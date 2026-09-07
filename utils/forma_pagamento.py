FORMAS_PAGAMENTO = (
    "PIX",
    "Débito",
    "Crédito",
    "Dinheiro",
    "Outro",
)


_ALIASES = {
    "PIX": "PIX",
    "DEBITO": "Débito",
    "DÉBITO": "Débito",
    "CREDITO": "Crédito",
    "CRÉDITO": "Crédito",
    "CARTAO": "Crédito",
    "CARTÃO": "Crédito",
    "CARTAO DE CREDITO": "Crédito",
    "CARTÃO DE CRÉDITO": "Crédito",
    "DINHEIRO": "Dinheiro",
    "OUTRO": "Outro",
}


def normalizar_forma_pagamento(valor):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError("Forma de pagamento inválida.")

    chave = " ".join(valor.strip().upper().split())
    forma = _ALIASES.get(chave)
    if forma is None:
        raise ValueError(
            "Forma de pagamento inválida. Use: "
            + ", ".join(FORMAS_PAGAMENTO)
            + "."
        )

    return forma
