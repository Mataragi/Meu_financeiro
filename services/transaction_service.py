from uuid import uuid4

from utils.status import (
    STATUS_PAGO,
    STATUS_PENDENTE,
    normalizar_status,
    normalizar_status_para_persistencia,
)


MESES_ORDEM = [
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
]


def normalizar_dados_transacao(dados):
    if "status" not in dados:
        return dados

    return {
        **dados,
        "status": normalizar_status_para_persistencia(dados["status"]),
    }


def normalizar_transacoes_dataframe(df):
    if "status" in df.columns:
        df["status"] = df["status"].map(normalizar_status)

    return df


def carregar_transacoes(mes, ano, carregar_transacoes_persistidas):
    return normalizar_transacoes_dataframe(
        carregar_transacoes_persistidas(mes, ano)
    )


def criar_transacoes(dados, inserir_transacoes):
    if dados:
        dados_normalizados = [normalizar_dados_transacao(dado) for dado in dados]
        return inserir_transacoes(dados_normalizados)


def calcular_mes_ano_parcela(mes_inicial, ano_inicial, incremento):
    if mes_inicial not in MESES_ORDEM:
        raise ValueError(f"Mês inválido para parcelamento: {mes_inicial}")

    indice_mes = MESES_ORDEM.index(mes_inicial)
    novo_indice_total = indice_mes + incremento

    novo_ano = int(ano_inicial) + (novo_indice_total // 12)
    novo_mes = MESES_ORDEM[novo_indice_total % 12]

    return novo_mes, novo_ano


def criar_transacoes_parceladas(
    ano,
    mes,
    descricao,
    valor_total,
    tipo,
    status,
    categoria,
    total_parcelas,
    inserir_transacoes,
    vencimento=None,
):
    if total_parcelas <= 1:
        return criar_transacoes([{
            "ano": ano,
            "mes": mes,
            "descricao": descricao,
            "valor": valor_total,
            "tipo": tipo,
            "status": status,
            "categoria": categoria,
            "parcela_atual": 1,
            "total_parcelas": 1,
            "grupo_parcelamento": None,
            "vencimento": vencimento,
        }], inserir_transacoes)

    grupo = str(uuid4())
    valor_parcela = round(valor_total / total_parcelas, 2)
    registros = []

    for i in range(total_parcelas):
        mes_parcela, ano_parcela = calcular_mes_ano_parcela(mes, ano, i)

        registros.append({
            "ano": ano_parcela,
            "mes": mes_parcela,
            "descricao": f"{descricao} {i + 1}/{total_parcelas}",
            "valor": valor_parcela,
            "tipo": tipo,
            "status": status,
            "categoria": categoria,
            "parcela_atual": i + 1,
            "total_parcelas": total_parcelas,
            "grupo_parcelamento": grupo,
            "vencimento": vencimento,
        })

    return criar_transacoes(registros, inserir_transacoes)


def atualizar_transacao(id_registro, dados, atualizar_transacao_persistida):
    if id_registro and dados:
        dados_normalizados = normalizar_dados_transacao(dados)
        return atualizar_transacao_persistida(id_registro, dados_normalizados)


def dar_baixa_transacao(id_registro, atualizar_status_registro):
    if id_registro:
        status_normalizado = normalizar_status_para_persistencia(STATUS_PAGO)
        return atualizar_status_registro(id_registro, status_normalizado)


def dar_baixa_transacoes(ids, atualizar_status_multiplos):
    if ids:
        status_normalizado = normalizar_status_para_persistencia(STATUS_PAGO)
        return atualizar_status_multiplos(ids, status_normalizado)


def atualizar_status_transacoes(ids, status, atualizar_status_multiplos):
    if ids:
        status_normalizado = normalizar_status_para_persistencia(status)
        return atualizar_status_multiplos(ids, status_normalizado)


def clonar_transacoes_mes(
    origem_mes,
    origem_ano,
    destino_mes,
    destino_ano,
    carregar_transacoes_mes,
    inserir_transacoes,
):
    registros_origem = carregar_transacoes_mes(origem_mes, origem_ano)

    if not registros_origem:
        return 0

    novos = []

    for registro in registros_origem:
        # A resposta do Supabase é tipada como JSON, que também pode conter
        # valores escalares ou nulos. Aqui só copiamos registros (objetos).
        if not isinstance(registro, dict):
            continue

        novos.append({
            "ano": destino_ano,
            "mes": destino_mes,
            "descricao": registro["descricao"],
            "valor": registro["valor"],
            "tipo": registro["tipo"],
            "status": STATUS_PENDENTE,
            "categoria": registro.get("categoria", "Sem categoria"),
            "vencimento": registro.get("vencimento"),
        })

    criar_transacoes(novos, inserir_transacoes)
    return len(novos)
