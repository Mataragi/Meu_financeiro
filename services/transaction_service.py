from uuid import uuid4

from services import database
from services.cache import cache_data, invalidar_cache_consultas
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


@cache_data(ttl=30)
def carregar_dados(mes, ano=None):
    return normalizar_transacoes_dataframe(database.carregar_dados(mes, ano))


def inserir_dados(dados):
    if dados:
        dados_normalizados = [normalizar_dados_transacao(dado) for dado in dados]
        database.inserir_dados(dados_normalizados)
        invalidar_cache_consultas()


def gerar_backup_transacoes():
    return database.gerar_backup_transacoes()


def calcular_mes_ano_parcela(mes_inicial, ano_inicial, incremento):
    if mes_inicial not in MESES_ORDEM:
        raise ValueError(f"Mês inválido para parcelamento: {mes_inicial}")

    indice_mes = MESES_ORDEM.index(mes_inicial)
    novo_indice_total = indice_mes + incremento

    novo_ano = int(ano_inicial) + (novo_indice_total // 12)
    novo_mes = MESES_ORDEM[novo_indice_total % 12]

    return novo_mes, novo_ano


def inserir_parcelado(
    ano,
    mes,
    descricao,
    valor_total,
    tipo,
    status,
    categoria,
    total_parcelas,
    vencimento=None,
):
    if total_parcelas <= 1:
        return inserir_dados([{
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
        }])

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

    return inserir_dados(registros)


def atualizar_registro(id_registro, dados):
    if id_registro and dados:
        database.atualizar_registro(
            id_registro,
            normalizar_dados_transacao(dados),
        )
        invalidar_cache_consultas()


def dar_baixa_registro(id_registro):
    if id_registro:
        database.atualizar_status_registro(id_registro, STATUS_PAGO)
        invalidar_cache_consultas()


def dar_baixa_multiplos(ids):
    if ids:
        database.atualizar_status_multiplos(ids, STATUS_PAGO)
        invalidar_cache_consultas()


def atualizar_status_multiplos(ids, status):
    if ids:
        database.atualizar_status_multiplos(
            ids,
            normalizar_status_para_persistencia(status),
        )
        invalidar_cache_consultas()


def excluir_registro(id_registro):
    if id_registro:
        database.excluir_registro(id_registro)
        invalidar_cache_consultas()


def excluir_multiplos(ids):
    if ids:
        database.excluir_multiplos(ids)
        invalidar_cache_consultas()


def excluir_multiplos_do_mes(ids, mes):
    if ids:
        database.excluir_multiplos_do_mes(ids, mes)
        invalidar_cache_consultas()


def excluir_grupo_parcelamento(grupo_id):
    if grupo_id:
        database.excluir_grupo_parcelamento(grupo_id)
        invalidar_cache_consultas()


def excluir_mes(mes, ano):
    database.excluir_mes(mes, ano)
    invalidar_cache_consultas()


def clonar_mes(origem_mes, origem_ano, destino_mes, destino_ano):
    registros_origem = database.carregar_dados_mes(origem_mes, origem_ano)

    if not registros_origem:
        return 0

    novos = []
    for registro in registros_origem:
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

    inserir_dados(novos)
    return len(novos)
