# Financeiro Pro

# Sprint 03 — Formalização do Modelo Financeiro

**Status:** Planejada

**Objetivo:** transformar as regras financeiras já identificadas durante as Sprints 01 e 02 em um modelo explícito, consistente e testável antes de novas automações ou alterações estruturais no banco.

---

## 1. Motivo da Sprint

O Financeiro Pro já possui uma base arquitetural organizada e um fluxo seguro para receber transações externas. Entretanto, algumas regras importantes ainda estão registradas como decisões de produto, mas não possuem uma modelagem operacional completa no sistema.

As principais são:

- data da movimentação;
- competência/ciclo financeiro;
- vencimento;
- fechamento do ciclo;
- saldo transportado entre ciclos;
- compras no Crédito;
- transferências entre contas próprias;
- comportamento de dados incompletos em automações.

A Sprint 03 não terá como objetivo adicionar muitas funcionalidades. O foco será definir a verdade financeira do sistema antes de automatizá-la.

---

## 2. Princípio central

```text
Regra financeira
      ↓
Modelo explícito
      ↓
Testes
      ↓
Implementação controlada
      ↓
Interface / automação
```

Nenhuma regra será implementada apenas porque parece intuitiva. Quando houver mais de uma interpretação possível, a decisão deverá ser registrada antes do código.

---

## 3. Itens da Sprint

| Item | Tarefa | Prioridade | Status |
|---|---|---|---|
| 1 | Formalizar data da movimentação, competência e vencimento | 🔴 | ⏳ |
| 2 | Formalizar regra completa do ciclo financeiro | 🔴 | ⏳ |
| 3 | Definir modelo de saldo real, pendências e saldo transportado | 🔴 | ⏳ |
| 4 | Formalizar comportamento de Crédito e pagamento de fatura | 🔴 | ⏳ |
| 5 | Definir tratamento de transferências entre contas próprias | 🟠 | ⏳ |
| 6 | Formalizar contrato definitivo para lançamentos externos | 🟠 | ⏳ |
| 7 | Criar testes das regras financeiras formalizadas | 🔴 | ⏳ |

---

## 4. Item 1 — Data da movimentação, competência e vencimento

Objetivo:

Definir sem ambiguidade a diferença entre:

- `data_transacao`: quando a operação ocorreu;
- `mes` + `ano`: ciclo/competência financeira ao qual o lançamento pertence;
- `vencimento`: dia em que a obrigação deve ser paga, quando aplicável.

Regra já estabelecida:

```text
data_transacao ≠ criado_em
```

`criado_em` representa o momento em que o registro foi criado e não deve ser usado como data da operação financeira.

Exemplo já confirmado:

```text
31/08/2026
    ↓
data_transacao

SETEMBRO/2026
    ↓
competência financeira
```

A Sprint deverá transformar essa distinção em regra operacional completa.

---

## 5. Item 2 — Ciclo financeiro

Objetivo:

Formalizar a regra de fechamento utilizada pelo usuário.

Regra conhecida:

- recebimento principal ocorre no dia 30;
- operações dos dias 30 e 31 podem pertencer ao ciclo seguinte.

Exemplo:

```text
31/08/2026 → ciclo SETEMBRO/2026
```

A definição deverá responder também:

- o que acontece com operações do dia 30;
- o que acontece com operações do dia 1;
- como entradas são tratadas;
- como saídas são tratadas;
- como parcelamentos respeitam o ciclo;
- como a competência é calculada quando houver informação de fatura.

Nenhuma dessas regras será automatizada antes da decisão formal.

---

## 6. Item 3 — Saldo real, pendências e transporte entre ciclos

Objetivo:

Separar claramente conceitos que hoje podem ser confundidos pelo cálculo atual.

O modelo a ser avaliado deverá distinguir, no mínimo:

```text
Saldo de abertura
+ Entradas efetivamente recebidas
- Saídas efetivamente pagas
= Saldo real
```

E, separadamente:

```text
Saldo real
- Obrigações pendentes
+ Entradas previstas
= visão projetada
```

Também deverá ser definido como o saldo de encerramento de um ciclo se torna saldo de abertura do ciclo seguinte.

A Sprint não deverá alterar o cálculo atual sem uma decisão explícita e testes de regressão.

---

## 7. Item 4 — Crédito e pagamento da fatura

Regra já aprovada:

```text
Compra no Crédito
        ↓
Pendente
        ↓
Fatura paga
        ↓
Pago
```

Exemplo:

```text
Compra: setembro
Fatura: outubro
Vencimento: dia 5

→ competência financeira: outubro
→ status inicial: Pendente
→ pagamento da fatura: transação passa para Pago
```

A Sprint deverá definir como representar de forma consistente:

- data real da compra;
- ciclo da fatura;
- vencimento;
- baixa da fatura;
- impacto no saldo;
- compras parceladas no Crédito.

---

## 8. Item 5 — Transferências entre contas próprias

Objetivo:

Evitar que transferências entre contas do próprio usuário sejam interpretadas como renda ou despesa.

O modelo deverá distinguir, quando aplicável:

```text
Entrada real
Saída real
Transferência interna
```

A criação do domínio completo de contas não faz parte automaticamente desta Sprint. Primeiro será definida a regra mínima necessária para que transferências internas não distorçam o fluxo financeiro.

---

## 9. Item 6 — Contrato definitivo de lançamentos externos

O contrato atual da Sprint 02 é provisório.

Após as regras financeiras serem formalizadas, deverão ser revisados os campos obrigatórios e condicionais para fontes externas.

O contrato deverá impedir que uma fonte externa invente ou complete silenciosamente informações financeiras ausentes.

Especial atenção:

- forma de pagamento;
- data da movimentação;
- competência;
- vencimento;
- crédito;
- transferências internas;
- dados ambíguos.

---

## 10. Item 7 — Testes das regras financeiras

Cada regra formalizada deverá possuir cobertura automatizada antes de ser incorporada ao comportamento principal.

Os testes deverão priorizar casos de borda, especialmente:

- dias 30 e 31;
- virada de ano;
- Crédito entre ciclos;
- vencimentos;
- entradas pendentes;
- saídas pendentes;
- saldo transportado;
- transferências internas;
- dados externos incompletos.

---

## 11. Fora do escopo inicial

Não fazem parte desta Sprint, salvo decisão posterior:

- migração completa do histórico para `forma_pagamento`;
- criação de contas bancárias completas;
- Open Finance;
- API pública;
- webhook;
- automação sem confirmação;
- migração para Flutter;
- redesign visual amplo.

Esses itens dependem das decisões financeiras e arquiteturais desta Sprint ou pertencem a fases posteriores.

---

## 12. Critério de conclusão

A Sprint 03 somente será considerada concluída quando:

```text
As regras financeiras estiverem definidas
          ↓
As ambiguidades críticas estiverem resolvidas
          ↓
As decisões estiverem documentadas
          ↓
As regras principais possuírem testes
          ↓
O modelo estiver pronto para implementação controlada
```

A Sprint não exige que todas as regras sejam imediatamente aplicadas ao banco. O objetivo principal é eliminar ambiguidades antes de automatizar o comportamento financeiro.

---

## 13. Resultado esperado

Ao final da Sprint 03, o Financeiro Pro deverá possuir uma definição clara de:

- quando uma movimentação acontece;
- a qual ciclo ela pertence;
- quando uma obrigação vence;
- o que compõe o saldo real;
- o que é pendência;
- como o saldo é transportado;
- como o Crédito se comporta;
- como transferências próprias são tratadas;
- quais informações uma automação externa pode ou não preencher.

Isso servirá como base para as próximas evoluções de UX, automação e futura migração de interface.
