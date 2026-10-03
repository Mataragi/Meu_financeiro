import pytest

from utils.forma_pagamento import normalizar_forma_pagamento


def test_normalizar_forma_pagamento_rejeita_valor_invalido():
    with pytest.raises(ValueError, match="Forma de pagamento inválida"):
        normalizar_forma_pagamento("Transferência")
