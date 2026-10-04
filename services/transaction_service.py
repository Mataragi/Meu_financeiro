from datetime import date, datetime
import math
from uuid import uuid4

from services import database
from services.cache import cache_data, invalidar_cache_consultas
from utils.forma_pagamento import normalizar_forma_pagamento
from utils.status import (
    STATUS_PAGO,
    STATUS_PENDENTE,
    normalizar_status,
    normalizar_status_para_persistencia,
)
from utils.tipo_transacao import normalizar_tipo, normalizar_tipos_dataframe


MESES_ORDEM = [
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
]


def normalizar_data_transacao(valor):
    if valor is None or valor == "":
        return None

    if isinstance(valor, datetime):
        return valor.date().isoformat()

    if isinstance(valor, date):
        return valor.isoformat()

    if isinstance(valor, str):
        try:
            return date.fromisoformat(valor.strip()).isoformat()
        except ValueError as exc:
            raise ValueError("Data da transação inválida.") from exc

    raise ValueError("Data da transação inválida.")


def calcular_competencia_credito(data_transacao):
    """Calcula mês e ano da fatura a partir da data real da compra."""
    data_normalizada = normalizar_data_transacao(data_transacao)
    if data_normalizada is None:
        raise ValueError("Data da transação é necessária para calcular a competência do Crédito.")

    data = date.fromisoformat(data_normalizada)
    incremento = 0 if data.day <= 4 else 1
    return calcular_mes_ano_parcela(
        MESES_ORDEM[data.month - 1],
        data.year,
        incremento,
    )


def normalizar_dados_transacao(dados):
    normalizados = dict(dados)

    if "tipo" in normalizados:
        normalizados["tipo"] = normalizar_tipo(normalizados["tipo"])

    if "status" in normalizados:
        normalizados["status"] = normalizar_status_para_persistencia(
            normalizados["status"]
        )

    if "forma_pagamento" in normalizados and normalizados["forma_pagamento"] is not None:
        normalizados["forma_pagamento"] = normalizar_forma_pagamento(
            normalizados["forma_pagamento"]
        )

    if "data_transacao" in normalizados:
        normalizados["data_transacao"] = normalizar_data_transacao(
            normalizados["data_transacao"]
        )

    return normalizados


def normalizar_transacoes_dataframe(df):
    df = normalizar_tipos_dataframe(df)
    if "status" in df.columns:
        df["status"] = df["status"].map(normalizar_status)

    return df


@cache_data(ttl=30)
def carregar_dados(mes, ano=None):
    return normalizar_transacoes_dataframe(database.carregar_dados(mes, ano))


def inserir_dados(dados):
    if dados:
        dados_normalizados = [
            normalizar_dados_transacao(dado) for dado in dados
        ]
        database.inserir_dados(dados_normalizados)
        invalidar_cache_consultas()


def inserir_ocorrencia_recorrencia(dados):
    """Persiste uma transação vinculada a uma ocorrência idempotente."""
    if not isinstance(dados, dict):
        raise ValueError("Dados da ocorrência inválidos.")

    recorrencia_id = dados.get("recorrencia_id")
    competencia_ocorrencia = dados.get("competencia_ocorrencia")
    if recorrencia_id is None or competencia_ocorrencia is None:
        raise ValueError(
            "recorrencia_id e competencia_ocorrencia são obrigatórios."
        )

    if isinstance(recorrencia_id, bool):
        raise ValueError("recorrencia_id inválido.")

    try:
        recorrencia_id = int(recorrencia_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("recorrencia_id inválido.") from exc

    competencia_normalizada = normalizar_data_transacao(competencia_ocorrencia)
    if competencia_normalizada is None:
        raise ValueError("competencia_ocorrencia inválida.")

    dados_normalizados = normalizar_dados_transacao(dados)
    dados_normalizados["recorrencia_id"] = recorrencia_id
    dados_normalizados["competencia_ocorrencia"] = competencia_normalizada

    resposta = database.inserir_transacao_recorrencia(dados_normalizados)
    invalidar_cache_consultas()
    return resposta


def _valor_ausente(valor):
    if valor is None:
        return True

    try:
        return math.isnan(valor)
    except (TypeError, ValueError):
        return False


def _recorrencia_informada(registro):
    return isinstance(registro, dict) and not _valor_ausente(
        registro.get("recorrencia_id")
    )


def _carregar_transacoes_por_ids(ids):
    ids_validos = [id_registro for id_registro in ids if id_registro]
    if not ids_validos:
        return []
    return database.carregar_transacoes_por_ids(ids_validos)


def _validar_baixa(valor, status):
    if status == STATUS_PAGO and _valor_ausente(valor):
        raise ValueError("Transações sem valor não podem ser marcadas como pagas.")


def _validar_baixa_em_registros(registros):
    for registro in registros:
        _validar_baixa(registro.get("valor"), STATUS_PAGO)


def _validar_exclusao(registros):
    if any(_recorrencia_informada(registro) for registro in registros):
        raise ValueError(
            "Ocorrências recorrentes não podem ser excluídas manualmente."
        )


def _forma_pagamento_para_duplicacao(registro):
    forma_pagamento = registro.get("forma_pagamento")
    if forma_pagamento is None:
        return None

    try:
        return normalizar_forma_pagamento(forma_pagamento)
    except ValueError:
        # Registros anteriores à validação podem conter valores legados.
        # A cópia trata a forma incompatível como ausente sem tocar no original.
        return None


def _data_transacao_ausente(valor):
    if valor is None or valor == "":
        return True

    try:
        return bool(valor != valor)
    except (TypeError, ValueError):
        return False


def _normalizar_vencimento_para_duplicacao(valor):
    if _data_transacao_ausente(valor):
        return None

    if isinstance(valor, bool):
        raise ValueError("Vencimento inválido.")

    if isinstance(valor, str):
        valor = valor.strip()
        if not valor:
            return None

    try:
        numero = float(valor)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Vencimento inválido.") from exc

    if not math.isfinite(numero) or not numero.is_integer():
        raise ValueError("Vencimento inválido.")

    vencimento = int(numero)
    if not 1 <= vencimento <= 31:
        raise ValueError("Vencimento inválido.")

    return vencimento


def duplicar_registro(registro, destino_mes, destino_ano):
    if not registro:
        raise ValueError("Registro obrigatório para duplicação")

    if destino_mes not in MESES_ORDEM:
        raise ValueError(f"Mês inválido para duplicação: {destino_mes}")

    novo_registro = {
        "ano": int(destino_ano),
        "mes": destino_mes,
        "descricao": registro.get("descricao", ""),
        "valor": registro.get("valor", 0),
        "tipo": registro.get("tipo", "Despesa"),
        "status": STATUS_PENDENTE,
        "categoria": registro.get("categoria", "Sem categoria"),
        "vencimento": _normalizar_vencimento_para_duplicacao(
            registro.get("vencimento")
        ),
    }

    forma_pagamento = _forma_pagamento_para_duplicacao(registro)
    if forma_pagamento is not None:
        novo_registro["forma_pagamento"] = forma_pagamento
    valor_data_transacao = registro.get("data_transacao")
    if not _data_transacao_ausente(valor_data_transacao):
        data_transacao = normalizar_data_transacao(valor_data_transacao)
        if data_transacao is not None:
            novo_registro["data_transacao"] = data_transacao

    inserir_dados([novo_registro])
    return novo_registro


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
    forma_pagamento=None,
    data_transacao=None,
):
    forma_normalizada = (
        normalizar_forma_pagamento(forma_pagamento)
        if forma_pagamento is not None
        else None
    )
    data_normalizada = normalizar_data_transacao(data_transacao)
    status_inicial = normalizar_status_para_persistencia(status)

    if forma_normalizada == "Crédito" and data_normalizada is not None:
        mes, ano = calcular_competencia_credito(data_normalizada)

    if forma_normalizada == "Crédito":
        status_inicial = STATUS_PENDENTE

    if total_parcelas <= 1:
        return inserir_dados([{
            "ano": ano,
            "mes": mes,
            "descricao": descricao,
            "valor": valor_total,
            "tipo": tipo,
            "status": status_inicial,
            "categoria": categoria,
            "parcela_atual": 1,
            "total_parcelas": 1,
            "grupo_parcelamento": None,
            "vencimento": vencimento,
            "forma_pagamento": forma_normalizada,
            "data_transacao": data_normalizada,
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
            "status": status_inicial,
            "categoria": categoria,
            "parcela_atual": i + 1,
            "total_parcelas": total_parcelas,
            "grupo_parcelamento": grupo,
            "vencimento": vencimento,
            "forma_pagamento": forma_normalizada,
            "data_transacao": data_normalizada,
        })

    return inserir_dados(registros)


def atualizar_registro(id_registro, dados):
    if id_registro and dados:
        campos_identidade = {"recorrencia_id", "competencia_ocorrencia"}
        if campos_identidade.intersection(dados):
            raise ValueError(
                "A identidade da ocorrência recorrente não pode ser alterada."
            )

        registros = _carregar_transacoes_por_ids([id_registro])
        atual = registros[0] if registros else {}
        dados_normalizados = normalizar_dados_transacao(dados)
        status_final = dados_normalizados.get("status", atual.get("status"))
        valor_final = dados_normalizados.get("valor", atual.get("valor"))
        status_final = normalizar_status(status_final)
        _validar_baixa(valor_final, status_final)

        if (
            _recorrencia_informada(atual)
            and _valor_ausente(atual.get("valor"))
            and not _valor_ausente(valor_final)
            and status_final == STATUS_PAGO
        ):
            raise ValueError(
                "Ocorrências recorrentes devem permanecer pendentes após informar o valor."
            )

        database.atualizar_registro(
            id_registro,
            dados_normalizados,
        )
        invalidar_cache_consultas()


def dar_baixa_registro(id_registro):
    if id_registro:
        _validar_baixa_em_registros(_carregar_transacoes_por_ids([id_registro]))
        database.atualizar_status_registro(id_registro, STATUS_PAGO)
        invalidar_cache_consultas()


def dar_baixa_multiplos(ids):
    if ids:
        _validar_baixa_em_registros(_carregar_transacoes_por_ids(ids))
        database.atualizar_status_multiplos(ids, STATUS_PAGO)
        invalidar_cache_consultas()


def atualizar_status_multiplos(ids, status):
    if ids:
        status_normalizado = normalizar_status_para_persistencia(status)
        if status_normalizado == STATUS_PAGO:
            _validar_baixa_em_registros(_carregar_transacoes_por_ids(ids))
        database.atualizar_status_multiplos(
            ids,
            status_normalizado,
        )
        invalidar_cache_consultas()


def excluir_registro(id_registro):
    if id_registro:
        _validar_exclusao(_carregar_transacoes_por_ids([id_registro]))
        database.excluir_registro(id_registro)
        invalidar_cache_consultas()


def excluir_multiplos(ids):
    if ids:
        _validar_exclusao(_carregar_transacoes_por_ids(ids))
        database.excluir_multiplos(ids)
        invalidar_cache_consultas()


def excluir_multiplos_do_mes(ids, mes):
    if ids:
        _validar_exclusao(_carregar_transacoes_por_ids(ids))
        database.excluir_multiplos_do_mes(ids, mes)
        invalidar_cache_consultas()


def excluir_grupo_parcelamento(grupo_id):
    if grupo_id:
        _validar_exclusao(
            database.carregar_transacoes_por_grupo_parcelamento(grupo_id)
        )
        database.excluir_grupo_parcelamento(grupo_id)
        invalidar_cache_consultas()


def excluir_mes(mes, ano):
    _validar_exclusao(
        database.carregar_dados(mes, ano).to_dict(orient="records")
    )
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

        novo = {
            "ano": destino_ano,
            "mes": destino_mes,
            "descricao": registro["descricao"],
            "valor": registro["valor"],
            "tipo": registro["tipo"],
            "status": STATUS_PENDENTE,
            "categoria": registro.get("categoria", "Sem categoria"),
            "vencimento": registro.get("vencimento"),
        }
        if registro.get("forma_pagamento") is not None:
            novo["forma_pagamento"] = registro.get("forma_pagamento")
        if registro.get("data_transacao") is not None:
            novo["data_transacao"] = registro.get("data_transacao")
        novos.append(novo)

    inserir_dados(novos)
    return len(novos)
