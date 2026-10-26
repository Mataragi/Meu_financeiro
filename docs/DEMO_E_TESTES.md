# Ambiente de testes e demonstrações

## Testes automatizados

Execute a suíte com o ambiente virtual do projeto:

```bash
.venv/bin/python -m pytest -q
```

Os testes devem usar mocks e dados fictícios. Não configure credenciais de produção nos testes e não execute testes de escrita contra o banco real.

## Ambiente de demonstração

O modo de demonstração seleciona explicitamente um projeto Supabase separado. Ele não usa as credenciais de produção como fallback.

1. Crie um projeto Supabase exclusivo para demonstração.
2. Aplique ao projeto demo o schema e as migrations necessários para a versão atual do app.
3. Copie `.streamlit/secrets.demo.toml.example` para referência e adicione o bloco `[demo]` ao `.streamlit/secrets.toml` local (arquivo de segredos, não versionado), preenchendo `SUPABASE_URL` e `SUPABASE_KEY` do projeto demo.
4. Inicie o app com `FINANCEIRO_PRO_ENV=demo` no ambiente do processo.

Exemplo no WSL:

```bash
FINANCEIRO_PRO_ENV=demo .venv/bin/streamlit run app.py
```

Se as credenciais `[demo]` estiverem ausentes, o app deve falhar explicitamente em vez de conectar à produção.

**Importante:** o projeto demo precisa conter apenas dados fictícios. Não copie dados pessoais ou financeiros de produção para o ambiente de demonstração. A preparação automática de dados de exemplo depende de validar o schema completo da tabela `transacoes`; não execute scripts de seed improvisados contra produção.
