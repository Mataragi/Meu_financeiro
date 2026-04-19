import pandas as pd

def tratar_valor(v):
    return float(v.replace('.', '').replace(',', '.'))

def ler_extrato(arq):
    df = pd.read_csv(arq, sep=';', encoding='latin1', on_bad_lines='skip')

    if 'Data' not in df.columns:
        for i, row in df.iterrows():
            if 'Data' in str(row.values):
                df.columns = df.iloc[i]
                df = df.iloc[i+1:].reset_index(drop=True)
                break

    df.columns = df.columns.str.strip()

    if 'Data' in df.columns:
        df = df.dropna(subset=['Data'])
        df = df[df['Data'].astype(str).str.contains('/')]

    return df

def processar_extrato(df):
    registros = []

    for _, row in df.iterrows():
        try:
            hist = str(row.iloc[1])
            A = str(row.iloc[3])
            B = str(row.iloc[4])

            if B not in ['nan','0,00','0','']:
                valor = abs(tratar_valor(B))
                tipo = "saída"
            elif A not in ['nan','0,00','0','']:
                valor = tratar_valor(A)
                tipo = "entrada"
            else:
                continue

            registros.append({
                "mes":"ABRIL",
                "descricao":hist,
                "valor":valor,
                "tipo":tipo,
                "status":"pago"
            })
        except:
            continue

    return registros