| Item | Tarefa                          | Prioridade | Status |
| ---- | ------------------------------- | ---------- | ------ |
| 1    | Remover Supabase dos Components | 🔴         | ✅    |
| 2    | Corrigir Parcelamentos          | 🔴         | ✅    |
| 3    | Centralizar Cache               | 🔴         | ✅    |
| 4    | Padronizar Status               | 🔴         | ⏳     |
| 5    | Refatorar `database.py`         | 🔴         | ⏳     |
| 6    | Criar Testes Essenciais         | 🔴         | ⏳     |

# Sprint 01 — Consolidação da Arquitetura

## Objetivo

Alinhar a implementação do Financeiro Pro com a arquitetura oficial do projeto,
eliminando inconsistências entre componentes, services e regras de negócio.

Nenhuma funcionalidade nova será implementada nesta sprint.

---

# Status

- Início: 18/07/2026
- Fim: __/__/____

Situação:
🟡 Em andamento

---

# Origem

Esta sprint foi criada a partir da Auditoria de Engenharia da versão 0.9.

A auditoria concluiu que a arquitetura do projeto está correta, porém existem
alguns pontos onde a implementação ainda não segue os padrões definidos na documentação.

---

# Escopo

## P1 — Crítico
### ☐ 1. Remover acesso direto ao Supabase dos Components

Prioridade:
🔴 Alta

Objetivo:

Components nunca devem acessar o banco.

Fluxo esperado:

Component

↓

Services

↓

Supabase

Critério:

☐ Dashboard

☐ Sidebar

☐ Backup

---


### ✅ 2. Corrigir Parcelamentos

Prioridade:
🔴 Alta

Objetivo:

Garantir que o status escolhido pelo usuário seja respeitado
ou documentar oficialmente uma regra diferente.

Critério de conclusão:

☑ Parcelamento respeita a regra definida

☑ Documentação atualizada

---

### ✅ 3. Centralizar Invalidação de Cache

Prioridade:
🔴 Alta

Objetivo:

Toda operação de escrita deve invalidar o cache automaticamente.

Critério:

☑ Inserção

☑ Exclusão

☑ Baixa

☑ Edição

---

### ☐ 4. Padronizar Status

Prioridade:
🔴 Alta

Objetivo:

Padronizar os valores persistidos para status das transações.

Problema atual:

- Pago
- pago
- Pendente
- pendente

Resultado esperado:

Somente um padrão será utilizado em toda aplicação.

Critério de conclusão:

☐ Mobile atualizado

☐ Desktop atualizado

☐ Banco consistente

☐ Filtros funcionando

---

### ☐ 5. Refatorar database.py

Prioridade:
🔴 Alta

Objetivo:

Separar:

- Persistência
- Interface
- Cache
- Regras de negócio

Critério:

☐ Nenhum st.success()

☐ Nenhum st.warning()

☐ Nenhum st.rerun()

☐ Apenas lógica de persistência

---

### ☐ 6. Criar Testes Essenciais

Prioridade:
🔴 Alta

Cobertura mínima:

☐ Parcelamentos

☐ Status

☐ Saldo

☐ Datas

☐ Parser CSV

---

# Fora do Escopo

Esta sprint NÃO contempla:

❌ Timeline

❌ Patrimônio

❌ Importador Inteligente

❌ Multiusuário

❌ Flutter

❌ API

---

# Critérios para concluir a Sprint

A Sprint será considerada concluída quando:

☑ Todos os itens P1 estiverem concluídos.

☑ O projeto continuar funcionando sem regressões.

☑ A documentação for atualizada.

☑ O CHANGELOG for atualizado.

☑ Um novo commit de consolidação for realizado.

---

# Resultado Esperado

Ao final desta sprint:

- A arquitetura documentada refletirá a implementação.
- O fluxo de dados será único.
- Mobile e Desktop utilizarão as mesmas regras financeiras.
- A base estará preparada para a Sprint 02.
