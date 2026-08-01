STATUS_PAGO = "Pago"
STATUS_PENDENTE = "Pendente"
STATUS_VALIDOS = {STATUS_PAGO, STATUS_PENDENTE}


def normalizar_status(status):
    """Converte valores legados de status para o padrão de exibição."""
    valor = str(status).strip().casefold()

    if valor == "pago":
        return STATUS_PAGO
    if valor == "pendente":
        return STATUS_PENDENTE

    return status


def normalizar_status_para_persistencia(status):
    """Garante que somente status oficiais sejam enviados ao banco."""
    status_normalizado = normalizar_status(status)

    if status_normalizado not in STATUS_VALIDOS:
        raise ValueError("Status inválido. Use 'Pago' ou 'Pendente'.")

    return status_normalizado
