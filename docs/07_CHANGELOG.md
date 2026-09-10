# Financeiro Pro

# Changelog

Todas as mudanças relevantes deste projeto serão documentadas neste arquivo.

O formato deste documento é inspirado no padrão **Keep a Changelog**.

---

# [Unreleased]

## Added

- Central de Ferramentas no Mobile com backup e restauração de backup.
- Ações contextuais por transação no Mobile com edição, exclusão e duplicação.
- Registrador de transações externas em `services/external_transaction_service.py`, com validação, normalização e proteção determinística contra duplicidade.
- Campos `data_transacao` e `forma_pagamento` no domínio de transações.
- Porta `services/chatgpt_bridge.py` para receber payloads estruturados produzidos pelo ChatGPT e encaminhá-los ao fluxo oficial.
- Etapa de preparação de transações externas sem persistência até a confirmação explícita do usuário.
- Revalidação e nova checagem de duplicidade no momento da confirmação antes da persistência.
- Teste ponta a ponta do fluxo ChatGPT → preparação → confirmação → Transaction Service → Repository.
- Formalização da ação futura `Pagar Fatura` como baixa em lote dos lançamentos de Crédito pendentes da competência selecionada.

## Changed

- Aplicação principal passou a iniciar exclusivamente a interface Mobile.
- A lista de transações do Mobile deixou de usar tabela para apresentar registros em cartões expansíveis, mantendo as ações individuais ocultas até a interação do usuário.
- `database.py` foi consolidado como Repository de persistência, sem acoplamento com Streamlit.
- Regras de transações foram centralizadas em `transaction_service.py` e a infraestrutura de cache foi isolada.
- Components passaram a acessar transações e dívidas por meio dos Services correspondentes.
- A documentação funcional passou a separar categoria de forma de pagamento e registrar o tratamento específico das compras no Crédito.
- O contrato da automação externa passou a prever `forma_pagamento` como evolução necessária antes da integração automática.
- A visualização em tabela permanece como modo alternativo de conferência e análise, enquanto os cartões seguem como apresentação principal no Mobile.
- Flutter foi registrado como evolução futura da interface, sem transformar a etapa atual em uma reescrita visual do Streamlit.
- Novos lançamentos passam a registrar a data da operação separadamente da data de criação do registro.
- Compras com forma de pagamento `Crédito` são criadas como `Pendente`; a baixa para `Pago` ocorre somente após o pagamento da fatura.
- O histórico existente permanece preservado sem preenchimento automático de `forma_pagamento` ou `data_transacao`.
- A ponte ChatGPT passou a separar preparação e confirmação, evitando persistência automática durante a recepção do payload.
- Sprint 02 — Automação de Lançamentos — foi concluída após validação ponta a ponta do fluxo externo.
- Sprint 03 — Item 1 — formalizou a semântica de `data_transacao`, `mes` + `ano`, `vencimento` e `criado_em`, mantendo esses conceitos separados.
- Sprint 03 — Item 2 — formalizou o ciclo financeiro entre o recebimento principal atual e o dia anterior ao próximo recebimento principal.
- Sprint 03 — Item 3 — formalizou saldo de abertura, saldo real, pendências, saldo projetado, saldo de encerramento e saldo transportado entre ciclos.
- O saldo transportado passou a ser definido como relação entre ciclos, sem criação de transação artificial de `Fechamento`.
- O saldo inicial do primeiro ciclo passou a ser tratado conceitualmente como posição de abertura confirmada pelo usuário, separada das transações financeiras.
- Sprint 03 — Item 4 — formalizou a competência das compras no Crédito, o fechamento no dia 05, o parcelamento por competências e o fluxo de pagamento da fatura.
- Compras no Crédito feitas do dia 01 ao 04 pertencem à fatura do próprio mês; compras feitas do dia 05 em diante pertencem à fatura do mês seguinte.
- A primeira implementação de fatura será um agrupamento lógico por `tipo`, `forma_pagamento`, `mes` e `ano`, sem tabela física específica de `faturas`.
- Sprint 03 — Item 5 — formalizou que transferências entre contas do casal usadas apenas como rota de pagamento não serão registradas como novas receitas ou despesas.
- Movimentações entre a conta familiar e a corretora foram formalmente separadas do fluxo de receitas e despesas, evitando que aportes ou retiradas de patrimônio sejam contabilizados como despesa ou receita.
- O domínio completo de contas, investimentos e patrimônio permanece como evolução futura, sem criação de infraestrutura específica nesta Sprint.

## Fixed

- Nenhuma correção registrada.

---

# [0.9.0]

## Added

### Estrutura inicial

- Cadastro de transações.
- Edição de transações.
- Exclusão de transações.
- Dashboard financeiro.
- Parcelamentos automáticos.
- Importação de extratos.
- Backup.
- Dívidas informais.

### Arquitetura

- Modularização do projeto.
- Separação em components, services e utils.
- Integração com Supabase.

### Interface

- Interface Mobile.
- Interface Desktop.
