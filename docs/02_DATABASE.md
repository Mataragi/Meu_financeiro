# Financeiro Pro

# Database Documentation

**Versão:** 1.0
**Status:** Documento Vivo
**Última atualização:** Julho de 2026

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

Atualmente o sistema possui duas tabelas principais.

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
| criado_em | Data de criação |
| ano | Organização anual |
| mes | Organização mensal |
| descricao | Nome da movimentação |
| valor | Valor financeiro |
| tipo | Entrada ou Saída |
| status | Pago ou Pendente |
| categoria | Classificação financeira |
| vencimento | Dia do vencimento |
| parcela_atual | Parcela corrente |
| total_parcelas | Quantidade de parcelas |
| grupo_parcelamento | Identificador do grupo |

---

## Regras

Uma transação representa apenas um evento financeiro.

Nunca deve representar patrimônio.

Nunca deve representar saldo bancário.

Nunca deve representar saldo de investimentos.

---

## Estados permitidos

Status

- Pago
- Pendente

Tipo

- Entrada
- Saída

---

## Origens possíveis

Uma transação pode ser criada por:

- Cadastro manual
- Parcelamento
- Clonagem
- Importação de extrato
- Futuras recorrências

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

# 6. Tabela: dividas_informais

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

# 7. Relacionamentos

Atualmente não existem chaves estrangeiras entre tabelas.

A única relação lógica existente é:

```
transacoes

↓

grupo_parcelamento

↓

outras transações
```

---

# 8. Fluxo das Informações

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

# 9. Convenções

Todos os novos campos devem seguir:

- nomes em português;
- snake_case;
- significado claro;
- evitar abreviações.

---

# 10. Regras de Evolução

Novas funcionalidades devem criar novas tabelas apenas quando representarem um novo domínio.

Nunca criar tabelas apenas para facilitar consultas.

---

# 11. Domínios Planejados

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

# 12. Decisão Arquitetural Importante

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

# 13. Expansão Planejada

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

# 14. Princípios

O banco seguirá permanentemente os seguintes princípios.

✅ Não duplicar dados.

✅ Separar domínios.

✅ Preservar histórico.

✅ Evitar campos genéricos.

✅ Priorizar simplicidade.

---

# 15. Considerações Finais

O banco de dados do Financeiro Pro foi projetado para evoluir junto com o produto.

A expansão ocorrerá através da criação de novos domínios especializados e não pelo crescimento descontrolado da tabela principal.

Essa abordagem mantém a arquitetura organizada, reduz dívida técnica e prepara o sistema para futuras funcionalidades sem comprometer a simplicidade da aplicação.