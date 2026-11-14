from types import SimpleNamespace

from services import database


class _FakeRPC:
    def __init__(self, data):
        self.data = data

    def execute(self):
        return SimpleNamespace(data=self.data)


class _FakeSupabaseRPC:
    def __init__(self, data=None):
        self.data = data or []
        self.calls = []

    def rpc(self, function_name, params):
        self.calls.append((function_name, params))
        return _FakeRPC(self.data)


def test_database_liquidar_transacoes_chama_rpc_com_payload_fechado(monkeypatch):
    fake = _FakeSupabaseRPC(data=[{"id": 10, "status": "Pago"}])
    monkeypatch.setattr(database, "supabase", fake)

    resultado = database.liquidar_transacoes(
        [10, 11],
        "2026-11-14",
        {"descricao": "Conta quitada"},
    )

    assert resultado == [{"id": 10, "status": "Pago"}]
    assert fake.calls == [(
        "liquidar_transacoes",
        {
            "p_ids": [10, 11],
            "p_data_liquidacao": "2026-11-14",
            "p_atualizacoes": {"descricao": "Conta quitada"},
        },
    )]


def test_database_liquidar_transacoes_envia_objeto_vazio_por_padrao(monkeypatch):
    fake = _FakeSupabaseRPC()
    monkeypatch.setattr(database, "supabase", fake)

    assert database.liquidar_transacoes([10], "2026-11-14") == []
    assert fake.calls[0][1]["p_atualizacoes"] == {}
