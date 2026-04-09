import sqlite3

def criar_banco():
    # Conecta (ou cria) o arquivo do banco
    conn = sqlite3.connect('financeiro.db')
    cursor = conn.cursor()
    
    # Cria a tabela de transações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mes TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            tipo TEXT NOT NULL, -- 'entrada' ou 'saida'
            status TEXT NOT NULL -- 'pago' ou 'pendente'
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Banco de dados 'financeiro.db' pronto para o combate!")

if __name__ == "__main__":
    criar_banco()