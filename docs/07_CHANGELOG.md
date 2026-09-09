## Marcos do Projeto

### Julho/2026

- Primeira documentação completa.

- Arquitetura consolidada.

- Definição oficial dos domínios.

- Roadmap criado.

- Base preparada para evolução.

---

### Futuro

Primeira versão pública.

Primeiro usuário.

Primeiro deploy mobile.

Primeiro release 1.0.

# Financeiro Pro

# Changelog

Todas as mudanças relevantes deste projeto serão documentadas neste arquivo.

O formato deste documento é inspirado no padrão **Keep a Changelog**.

---

# [Unreleased]

## Added

- Central de Ferramentas no Mobile com backup e restauração de backup.
- Ações contextuais por transação no Mobile com edição, exclusão e duplicação.
- Registrador de transações externas em `services/external_transaction_service.py`,
  com validação, normalização e proteção determinística contra duplicidade.
- Campos `data_transacao` e `forma_pagamento` no domínio de transações.
- Porta `services/chatgpt_bridge.py` para receber payloads estruturados produzidos pelo ChatGPT e encaminhá-los ao fluxo oficial.
- Etapa de preparação de transações externas sem persistência até a confirmação explícita do usuário.
- Revalidação e nova checagem de duplicidade no momento da confirmação antes da persistência.
- Teste ponta a ponta do fluxo ChatGPT → preparação → confirmação → Transaction Service → Repository.

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
- Sprint 03 — Item 2 — formalizou o ciclo financeiro como o período entre um recebimento principal e o dia anterior ao próximo recebimento principal, acompanhando as datas reais dos recebimentos.

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
