import pytest

from services import supabase_client


def test_ambiente_production_usa_credenciais_padrao(monkeypatch):
    monkeypatch.setenv("FINANCEIRO_PRO_ENV", "production")
    monkeypatch.setattr(
        supabase_client.st,
        "secrets",
        {"SUPABASE_URL": "https://prod.example", "SUPABASE_KEY": "prod-key"},
    )

    assert supabase_client._configuracao_supabase() == (
        "https://prod.example",
        "prod-key",
    )


def test_ambiente_demo_usa_apenas_credenciais_demo(monkeypatch):
    monkeypatch.setenv("FINANCEIRO_PRO_ENV", "demo")
    monkeypatch.setattr(
        supabase_client.st,
        "secrets",
        {
            "SUPABASE_URL": "https://prod.example",
            "SUPABASE_KEY": "prod-key",
            "demo": {
                "SUPABASE_URL": "https://demo.example",
                "SUPABASE_KEY": "demo-key",
            },
        },
    )

    assert supabase_client._configuracao_supabase() == (
        "https://demo.example",
        "demo-key",
    )


def test_ambiente_demo_sem_credenciais_nao_cai_em_producao(monkeypatch):
    monkeypatch.setenv("FINANCEIRO_PRO_ENV", "demo")
    monkeypatch.setattr(
        supabase_client.st,
        "secrets",
        {"SUPABASE_URL": "https://prod.example", "SUPABASE_KEY": "prod-key"},
    )

    with pytest.raises(RuntimeError, match="Configure um projeto Supabase exclusivo"):
        supabase_client._configuracao_supabase()


def test_ambiente_desconhecido_falha_com_seguranca(monkeypatch):
    monkeypatch.setenv("FINANCEIRO_PRO_ENV", "demoo")

    with pytest.raises(RuntimeError, match="FINANCEIRO_PRO_ENV inválido"):
        supabase_client._configuracao_supabase()
