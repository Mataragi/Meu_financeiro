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

## Changed

- Aplicação principal passou a iniciar exclusivamente a interface Mobile.
- A lista de transações do Mobile deixou de usar tabela para apresentar registros em cartões expansíveis, mantendo as ações individuais ocultas até a interação do usuário.
- `database.py` foi consolidado como Repository de persistência, sem acoplamento com Streamlit.
- Regras de transações foram centralizadas em `transaction_service.py` e a infraestrutura de cache foi isolada.
- Components passaram a acessar transações e dívidas por meio dos Services correspondentes.

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
