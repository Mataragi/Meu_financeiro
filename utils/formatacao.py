import math

from utils.status import STATUS_PAGO, STATUS_PENDENTE


def colorir_status(valor):
    if valor == STATUS_PENDENTE:
        return 'background-color: #ff4b4b; color: white'
    elif valor == STATUS_PAGO:
        return 'background-color: #28a745; color: white'
    return ''

def formatar_real(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return valor


def formatar_valor_exibicao(valor):
    if valor is None:
        return "Valor não informado"

    try:
        if math.isnan(valor):
            return "Valor não informado"
    except (TypeError, ValueError):
        pass

    return formatar_real(valor)
