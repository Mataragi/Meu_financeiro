from datetime import date

import pytest

from utils.liquidacao import validar_nova_liquidacao, validar_status_liquidacao


def test_pendente_com_liquidacao_e_rejeitado():
    with pytest.raises(ValueError, match="pendente não pode possuir"):
        validar_status_liquidacao("Pendente", date(2026, 10, 10))


def test_pago_com_liquidacao_e_normalizado():
    assert validar_status_liquidacao("Pago", date(2026, 10, 10)) == "2026-10-10"


def test_pago_legado_sem_liquidacao_e_aceito():
    assert validar_status_liquidacao("Pago", None) is None


def test_nova_transacao_paga_sem_liquidacao_e_rejeitada():
    with pytest.raises(ValueError, match="exige data efetiva"):
        validar_nova_liquidacao("Pago", None)
