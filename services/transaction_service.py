from uuid import uuid4

from utils.status import STATUS_PAGO, STATUS_PENDENTE


MESES_ORDEM = [
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
]


def criar_transacoes(dados, inserir_transacoes):
    if dados:
        return inserir_transacoes(dados)


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
        return atualizar_transacao_persistida(id_registro, dados)


def dar_baixa_transacao(id_registro, atualizar_status_registro):
    if id_registro:
        return atualizar_status_registro(id_registro, STATUS_PAGO)


def dar_baixa_transacoes(ids, atualizar_status_multiplos):
    if ids:
        return atualizar_status_multiplos(ids, STATUS_PAGO)


def atualizar_status_transacoes(ids, status, atualizar_status_multiplos):
    if ids:
        return atualizar_status_multiplos(ids, status)


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
