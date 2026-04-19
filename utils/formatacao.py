def colorir_status(valor):
    if str(valor).lower() == 'pendente':
        return 'background-color: #ff4b4b; color: white'
    elif str(valor).lower() == 'pago':
        return 'background-color: #28a745; color: white'
    return ''

def formatar_real(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return valor