# Financeiro Pro

# Database Documentation

**Versão:** 1.1
**Status:** Documento Vivo
**Última atualização:** Setembro de 2026

---

# 1. Objetivo

Este documento descreve toda a estrutura do banco de dados utilizada pelo Financeiro Pro.

Seu objetivo é documentar:

- tabelas;
- responsabilidades;
- relacionamentos;
- regras de negócio;
- fluxo dos dados;
- futuras expansões.

Este documento é a referência oficial para qualquer alteração estrutural no banco.

---

# 2. Filosofia do Banco

O banco foi projetado seguindo alguns princípios fundamentais.

## Fonte única da verdade

Sempre que possível, uma informação deverá existir em apenas um lugar.

Evitar duplicação de dados é prioridade.

---

## Histórico permanente

Movimentações financeiras representam eventos ocorridos.

Sempre que possível, devem ser preservadas.

Evitar apagar dados históricos.

---

## Separação de Domínios

Cada tabela representa apenas um domínio do sistema.

Exemplos:

- Fluxo financeiro
- Dívidas
- Patrimônio
- Recorrências

Misturar conceitos em uma única tabela deve ser evitado.

---

# 3. Modelo Atual

O sistema possui três tabelas principais.

```
transacoes

↓

Fluxo Financeiro
```

```
dividas_informais

↓

Controle de Dívidas
```

```
recorrencias

↓

Regras de geração futura
```

---

# 4. Tabela: transacoes

## Responsabilidade

Armazenar toda movimentação financeira do usuário.

Esta é a tabela mais importante do sistema.

Ela representa o fluxo financeiro.

---

## Utilizada por

- Dashboard
- Timeline
- Cadastro
- Parcelamentos
- Importação
- Backup
- Relatórios futuros

---

## Campos

| Campo | Finalidade |
|--------|------------|
| id | Identificador único |
| criado_em | Data de criação do registro |
| data_transacao | Data em que a operação aconteceu |
| ano | Ano do ciclo financeiro |
| mes | Mês do ciclo financeiro |
| descricao | Nome da movimentação |
| valor | Valor financeiro |
| tipo | Entrada ou Saída |
| status | Pago ou Pendente |
| categoria | O que foi gasto ou recebido |
| forma_pagamento | Como a movimentação foi paga ou recebida |
| vencimento | Dia do vencimento da obrigação |
| parcela_atual | Parcela corrente |
| total_parcelas | Quantidade de parcelas |
| grupo_parcelamento | Identificador do grupo |
| recorrencia_id | Regra de recorrência que originou o lançamento, quando aplicável |
| competencia_ocorrencia | Período lógico da ocorrência recorrente, quando aplicável |

`data_transacao` e `criado_em` possuem significados diferentes. `criado_em` registra quando o sistema criou o registro; `data_transacao` registra quando a operação ocorreu.

`mes` e `ano` representam o ciclo financeiro ao qual o lançamento pertence e não devem ser tratados automaticamente como a data da operação.

---

## Regras

Uma transação representa apenas um evento financeiro.

Nunca deve representar patrimônio.

Nunca deve representar saldo bancário.

Nunca deve representar saldo de investimentos.

A categoria e a forma de pagamento são conceitos independentes.

---

## Estados permitidos

Status

- Pago
- Pendente

Tipo

- Entrada
- Saída

Forma de pagamento

- PIX
- Débito
- Crédito
- Dinheiro
- Outro

Para uma nova compra com forma de pagamento `Crédito`, o status inicial é `Pendente`. Após o pagamento da fatura, o registro poderá ser marcado como `Pago` pelo fluxo oficial de baixa.

---

## Origens possíveis

Uma transação pode ser criada por:

- Cadastro manual
- Parcelamento
- Clonagem
- Importação de extrato
- Futuras recorrências
- Futuras fontes externas

---

## Destinos

A tabela alimenta:

- Dashboard
- Timeline
- Relatórios
- Indicadores
- Fluxo de Caixa

---

# 5. Parcelamentos

Parcelamentos não possuem tabela própria.

Cada parcela é armazenada como uma transação independente.

Todas compartilham o mesmo:

```
grupo_parcelamento
```

Exemplo

Compra

R$ 1.200

12 parcelas

↓

12 registros

↓

Mesmo UUID

↓

Parcelas individuais

---

## Motivo

Essa abordagem simplifica:

- filtros
- vencimentos
- baixa
- relatórios

---

# 6. Tabela: recorrencias

## Responsabilidade

Armazenar regras mensais de geração futura. A tabela não armazena pagamentos
nem substitui a tabela `transacoes`.

## Campos

| Campo | Finalidade |
|--------|------------|
| id | Identificador da regra |
| descricao | Descrição base do lançamento |
| valor | Valor fixo ou nulo quando ainda desconhecido |
| tipo | Receita ou Despesa |
| categoria | Categoria oficial |
| forma_pagamento | Forma oficial de pagamento |
| vencimento | Dia da obrigação, quando aplicável |
| periodicidade | Nesta etapa, somente Mensal |
| dia_programado | Dia da ocorrência mensal |
| data_inicio | Primeiro período permitido |
| data_fim | Último período permitido, opcional e inclusivo |
| status_recorrencia | Ativa, Pausada ou Cancelada |
| criado_em | Data de criação da regra |
| atualizado_em | Data da última alteração da regra |

`dia_programado` é separado de `vencimento`: vencimento continua representando
o dia da obrigação financeira, enquanto o novo campo representa o calendário
da regra recorrente.

As transações geradas recebem `recorrencia_id` e `competencia_ocorrencia`.
Transações manuais mantêm ambos os campos nulos.

Uma restrição única em `(recorrencia_id, competencia_ocorrencia)` prepara a
materialização idempotente. Como os dois campos são nulos para transações
manuais, a restrição não as agrupa como ocorrências recorrentes.

Esta etapa ainda não implementa sincronização, scheduler ou interface de
recorrências.

---

# 7. Tabela: dividas_informais

## Responsabilidade

Registrar empréstimos entre pessoas.

Esta tabela é completamente independente das transações.

---

## Campos

| Campo | Finalidade |
|--------|------------|
| id | Identificador |
| criado_em | Data |
| pessoa | Nome da pessoa |
| descricao | Descrição |
| valor | Valor |
| tipo | Eu devo / Me devem |
| status | Pago / Pendente |
| observacao | Texto livre |

---

## Utilização

A tabela é utilizada exclusivamente pelo módulo de Dívidas Informais.

---

# 8. Relacionamentos

As tabelas históricas não possuíam chaves estrangeiras entre si. A fundação de
Recorrências introduziu uma chave estrangeira opcional de `transacoes` para
`recorrencias`, usada somente por lançamentos recorrentes.

A única relação lógica existente é:

```
transacoes

↓

grupo_parcelamento

↓

outras transações
```

---

# 9. Fluxo das Informações

Cadastro

↓

Validação

↓

Service

↓

Supabase

↓

Tabela

↓

Cache

↓

Interface

---

# 10. Convenções

Todos os novos campos devem seguir:

- nomes em português;
- snake_case;
- significado claro;
- evitar abreviações.

---

# 11. Regras de Evolução

Novas funcionalidades devem criar novas tabelas apenas quando representarem um novo domínio.

Nunca criar tabelas apenas para facilitar consultas.

Alterações estruturais em `transacoes` devem preservar dados históricos sempre que possível.

---

# 12. Domínios Planejados

O Financeiro Pro deverá crescer através de novos domínios.

Não através da expansão infinita da tabela transacoes.

---

## Patrimônio

Responsável por armazenar ativos.

Exemplos

- Conta Corrente
- Poupança
- Corretora
- Criptomoedas
- Outros investimentos

---

## Recorrências

Responsável pelas regras de geração automática.

Não armazenará pagamentos.

Apenas regras.

---

## Metas Financeiras

Objetivos financeiros.

---

## Categorias Inteligentes

Regras automáticas de classificação.

---

## Caixa de Entrada Bancária

Movimentações importadas.

Ainda não categorizadas.

---

# 13. Decisão Arquitetural Importante

A tabela transacoes representa fluxo financeiro.

Ela NÃO representa patrimônio.

Exemplo

Salário

↓

Entrada

✔

Compra de Mercado

↓

Saída

✔

Transferência para Corretora

↓

Não é gasto.

É movimentação patrimonial.

No futuro será tratada por outro domínio.

Essa decisão evita distorções em:

- saldo
- indicadores
- relatórios

---

# 14. Expansão Planejada

Arquitetura futura

```
transacoes

↓

Fluxo Financeiro
```

```
dividas_informais

↓

Empréstimos
```

```
patrimonio

↓

Ativos
```

```
recorrencias

↓

Regras Automáticas
```

```
movimentacoes_bancarias

↓

Importações
```

```
metas

↓

Objetivos Financeiros
```

Cada tabela possuirá responsabilidade única.

---

# 15. Princípios

O banco seguirá permanentemente os seguintes princípios.

✅ Não duplicar dados.

✅ Separar domínios.

✅ Preservar histórico.

✅ Evitar campos genéricos.

✅ Priorizar simplicidade.

---

# 16. Considerações Finais

O banco de dados do Financeiro Pro foi projetado para evoluir junto com o produto.

A expansão ocorrerá através da criação de novos domínios especializados e não pelo crescimento descontrolado da tabela principal.

Essa abordagem mantém a arquitetura organizada, reduz dívida técnica e prepara o sistema para futuras funcionalidades sem comprometer a simplicidade da aplicação.
