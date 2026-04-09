import sqlite3

def migrar_forçado(nome_do_mes):
    # COLE SEUS DADOS AQUI (Copiei do seu print)
    dados = """
    CARRO 23(48) R$ 605,00
    SEGURO DO CARRO R$ 178,00
    CLARO LETÍCIA R$ 62,00
    VAN ESCOLAR R$ 220,00
    BABÁ R$ 239,00
    INTERNET R$ 100,00
    CAROL 5(8) R$ 135,00
    GÁS R$ 35,00
    MOCHILA ESCOLAR 3(10) R$ 54,00
    FINANCIAMENTO R$ 1.400,00
    CLARO LUCAS R$ 56,00
    PENSÃO R$ 730,00
    CONDOMINIO R$ 411,29
    CPFL R$ 292,96
    ACORDO CONDOMINIO 3(3) R$ 345,00
    FACULDADE LUCAS R$ 130,00
    IPTU 2(7) R$ 109,00
    IPVA 2(5) R$ 154,41
    BICICLETA ALICE 1(5) R$ 46,38
    REMEDIO ALICE R$ 118,00
    INSTRUMENT R$ 190,00
    PÁSCOA R$ 140,00
    SALÁRIO LUCAS R$ 1.900,00
    SALÁRIO LETICIA R$ 2.100,00
    """

    conn = sqlite3.connect('financeiro.db')
    cursor = conn.cursor()

    linhas = dados.strip().split('\n')
    for linha in linhas:
        if 'R$' in linha:
            partes = linha.split('R$')
            desc = partes[0].strip()
            valor = partes[1].replace('.', '').replace(',', '.').strip()
            
            # Forçamos o tipo: se tiver "SALÁRIO", é entrada.
            tipo = 'entrada' if 'SALÁRIO' in desc.upper() else 'saida'
            
            # AQUI ESTÁ O PULO DO GATO: mes=nome_do_mes.upper()
            cursor.execute("INSERT INTO transacoes (mes, descricao, valor, tipo, status) VALUES (?, ?, ?, ?, ?)",
                           (nome_do_mes.upper(), desc, float(valor), tipo, 'pago'))

    conn.commit()
    conn.close()
    print(f"🚀 Agora sim! Abril está populado.")

if __name__ == "__main__":
    migrar_forçado("ABRIL")