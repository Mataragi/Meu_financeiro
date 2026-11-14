# Ambiente de testes e demonstrações

## Testes automatizados

Execute a suíte com o ambiente virtual do projeto:

```bash
.venv/bin/python -m pytest -q
```

Os testes devem usar mocks e dados fictícios. Não configure credenciais de produção nos testes e não execute testes de escrita contra o banco real.

Os testes de integração PostgreSQL são opcionais na suíte normal e usam um
container local efêmero, sem URL, chave ou dados do Supabase. Para executá-los:

```bash
FINANCEIRO_PRO_TEST_POSTGRES=1 .venv/bin/python -m pytest -q tests/test_liquidacao_postgres_integration.py
```

Eles verificam a RPC de liquidação e não substituem a homologação em um projeto
Supabase de demonstração separado.

## Ambiente de demonstração

O modo de demonstração seleciona explicitamente um projeto Supabase separado. Ele não usa as credenciais de produção como fallback.

1. Crie um projeto Supabase exclusivo para demonstração.
2. Aplique ao projeto demo o schema e as migrations necessários para a versão atual do app.
3. Copie `.streamlit/secrets.demo.toml.example` para referência e adicione o bloco `[demo]` ao `.streamlit/secrets.toml` local (arquivo de segredos, não versionado), preenchendo `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` do projeto demo. A service-role key permanece somente no servidor Streamlit.
4. Inicie o app com `FINANCEIRO_PRO_ENV=demo` no ambiente do processo.

Exemplo no WSL:

```bash
FINANCEIRO_PRO_ENV=demo .venv/bin/streamlit run app.py
```

Se as credenciais `[demo]` estiverem ausentes, o app deve falhar explicitamente em vez de conectar à produção.

**Importante:** o projeto demo precisa conter apenas dados fictícios. Não copie dados pessoais ou financeiros de produção para o ambiente de demonstração. A preparação automática de dados de exemplo depende de validar o schema completo da tabela `transacoes`; não execute scripts de seed improvisados contra produção.
