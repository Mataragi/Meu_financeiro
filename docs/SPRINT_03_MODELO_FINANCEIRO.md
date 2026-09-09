# Financeiro Pro

# Sprint 03 — Formalização do Modelo Financeiro

**Status:** Em desenvolvimento

**Objetivo:** transformar as regras financeiras já identificadas durante as Sprints 01 e 02 em um modelo explícito, consistente e testável antes de novas automações ou alterações estruturais no banco.

---

## 1. Motivo da Sprint

O Financeiro Pro já possui uma base arquitetural organizada e um fluxo seguro para receber transações externas. Entretanto, algumas regras importantes ainda precisam de modelagem operacional completa.

A Sprint 03 formaliza:

- data da movimentação;
- competência/ciclo financeiro;
- vencimento;
- saldo de abertura;
- saldo real;
- saldo projetado;
- saldo transportado entre ciclos;
- compras no Crédito;
- transferências entre contas próprias;
- comportamento de dados incompletos em automações.

O foco é definir a verdade financeira do sistema antes de automatizá-la.

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
| 1 | Formalizar data da movimentação, competência e vencimento | 🔴 | ✅ |
| 2 | Formalizar regra completa do ciclo financeiro | 🔴 | ✅ |
| 3 | Definir modelo de saldo real, pendências e saldo transportado | 🔴 | ✅ |
| 4 | Formalizar comportamento de Crédito e pagamento de fatura | 🔴 | ⏳ |
| 5 | Definir tratamento de transferências entre contas próprias | 🟠 | ⏳ |
| 6 | Formalizar contrato definitivo para lançamentos externos | 🟠 | ⏳ |
| 7 | Criar testes das regras financeiras formalizadas | 🔴 | ⏳ |

---

## 4. Item 1 — Data da movimentação, competência e vencimento

**Status: Concluído.**

### 4.1 Definições oficiais

```text
data_transacao = fato financeiro ocorrido
mes + ano       = competência/ciclo financeiro
vencimento      = dia da obrigação, quando aplicável
criado_em       = momento de criação do registro
```

`data_transacao` não deve ser substituída por `criado_em`. `mes` + `ano` não precisam coincidir com o mês civil da operação.

### 4.2 Exemplo

Uma operação realizada em 31/08/2026 pode pertencer ao ciclo de setembro:

```text
31/08/2026 → data_transacao
SETEMBRO/2026 → mes + ano
```

### 4.3 Limites

Este item não implementa o cálculo automático da competência nem altera o banco. O comportamento específico de Crédito será aprofundado no Item 4.

---

## 5. Item 2 — Ciclo financeiro

**Status: Concluído.**

### 5.1 Regra oficial

Um ciclo financeiro começa no dia em que o recebimento principal ocorre e termina no dia anterior ao próximo recebimento principal.

```text
Recebimento principal A
        ↓
INÍCIO DO CICLO
        │
        │ operações do período
        │
        ↓
Dia anterior ao recebimento B
        ↓
FIM DO CICLO

Recebimento principal B
        ↓
INÍCIO DO PRÓXIMO CICLO
```

O ciclo não depende de o mês possuir 28, 29, 30 ou 31 dias.

### 5.2 Exemplo

```text
Recebimento: 30/08/2026
Próximo:     30/09/2026

Ciclo de SETEMBRO/2026:
30/08/2026 → 29/09/2026

Próximo ciclo:
30/09/2026 → 29/10/2026
```

O dia do recebimento inicia o novo ciclo. O dia anterior ao próximo recebimento encerra o ciclo atual.

### 5.3 Recebimento antecipado ou atrasado

O ciclo acompanha as datas reais. Se o próximo recebimento ocorrer em 29/09 em vez de 30/09, o ciclo anterior termina em 28/09 e o novo começa em 29/09.

### 5.4 Dia 1 e virada de ano

O dia 1 não reinicia o ciclo. Uma virada de ano também não interrompe artificialmente o período.

```text
Recebimento: 30/12/2026
Próximo:     30/01/2027

Ciclo:
30/12/2026 → 29/01/2027
```

### 5.5 Parcelamentos

Parcelamentos continuam sendo transações independentes. Cada parcela deverá possuir a competência/ciclo correspondente ao período financeiro ao qual pertence.

### 5.6 Limites

Este item define o período do ciclo. Não define saldo de abertura, transporte, projeção ou liquidação de Crédito. Esses comportamentos pertencem aos Itens 3 e 4.

---

## 6. Item 3 — Saldo real, pendências e transporte entre ciclos

**Status: Concluído.**

### 6.1 Diagnóstico

O cálculo atual não possui saldo de abertura, encerramento ou transporte formal. Entradas Pendentes são incluídas no saldo atual, enquanto Saídas Pendentes são ignoradas. Também não existe saldo projetado formal.

A nova regra foi formalizada sem alterar ainda o cálculo de produção.

### 6.2 Saldo de abertura

Para o primeiro ciclo controlado pelo sistema:

```text
Saldo de abertura = valor inicial informado e confirmado pelo usuário
```

Para os ciclos seguintes:

```text
Saldo de abertura do ciclo N+1
    = saldo de encerramento real do ciclo N
```

O saldo de abertura não deverá ser inferido pela soma das transações do ciclo atual.

### 6.3 Entradas realizadas

São somente as transações que atendem:

```text
tipo = Entrada
status = Pago
```

Entradas Pendentes não compõem o saldo real.

### 6.4 Saídas realizadas

São somente as transações que atendem:

```text
tipo = Saída
status = Pago
```

Saídas Pendentes não reduzem o saldo real.

### 6.5 Saldo real

```text
Saldo real =
    saldo de abertura
    + Entradas Pagas
    - Saídas Pagas
```

Esse valor representa o dinheiro efetivamente disponível ao final do ciclo, conforme os lançamentos conhecidos.

### 6.6 Pendências e valores previstos

```text
Obrigações pendentes = Σ Saídas Pendentes
Entradas previstas   = Σ Entradas Pendentes
```

Entrada Pendente representa recebimento esperado. Saída Pendente representa obrigação ainda não realizada.

### 6.7 Saldo projetado

```text
Saldo projetado =
    saldo real
    - Saídas Pendentes
    + Entradas Pendentes
```

Na primeira implementação, a projeção ficará restrita ao ciclo/horizonte explicitamente consultado. Projeção multi-ciclo será evolução futura.

### 6.8 Saldo de encerramento

```text
Saldo de encerramento = saldo real do ciclo
```

Pendências futuras não alteram o saldo de encerramento real. Elas afetam somente a visão projetada.

### 6.9 Transporte

```text
Saldo transportado do ciclo N
        ↓
Saldo de abertura do ciclo N+1
```

O transporte é uma relação entre ciclos, não uma nova movimentação financeira.

### 6.10 Tratamento do "Fechamento"

`Fechamento` não será tratado como tipo financeiro nem como mecanismo de transporte.

O encerramento é resultado calculado do ciclo. Registros históricos eventualmente chamados `Fechamento` não serão apagados ou convertidos automaticamente. Eles deverão ser auditados antes de qualquer migração.

### 6.11 Alterações retroativas

Como o saldo transportado é derivado do encerramento anterior, uma alteração retroativa em um ciclo deverá permitir recalcular os ciclos posteriores. O modelo não dependerá de saldos de abertura digitados de forma independente para cada ciclo.

### 6.12 Representação do primeiro saldo

O saldo inicial será tratado como posição de abertura, separada dos fatos financeiros de `transacoes`. A forma física de persistência será definida na implementação do modelo.

### 6.13 Casos que deverão ser cobertos posteriormente

Antes da implementação, os testes deverão contemplar:

- primeiro ciclo com saldo inicial positivo;
- primeiro ciclo com saldo inicial negativo;
- ciclo sem entradas ou sem saídas;
- Entradas Pagas e Pendentes;
- Saídas Pagas e Pendentes;
- saldo real negativo;
- saldo projetado negativo;
- transporte positivo e negativo;
- ciclo sem transações, mas com saldo transportado;
- ciclos iniciados nos dias 30 e 31;
- recebimento antecipado ou atrasado;
- virada de dezembro para janeiro;
- competência diferente de `data_transacao`;
- parcelamentos;
- Crédito pendente e posteriormente pago;
- registros históricos de `Fechamento`;
- alterações retroativas e exclusões que afetem ciclos anteriores.

### 6.14 Critério de aceite

O Item 3 é considerado formalizado quando o domínio distinguir:

```text
saldo de abertura
saldo real
obrigações pendentes
entradas previstas
saldo projetado
saldo de encerramento
saldo transportado
```

e quando o transporte entre ciclos não depender de uma transação artificial.

---

## 7. Item 4 — Crédito e pagamento da fatura

**Status: Pendente.**

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

A Sprint deverá definir de forma consistente:

- data real da compra;
- ciclo da fatura;
- vencimento;
- baixa da fatura;
- impacto no saldo;
- compras parceladas no Crédito.

---

## 8. Item 5 — Transferências entre contas próprias

**Status: Pendente.**

Objetivo: evitar que transferências entre contas do próprio usuário sejam interpretadas como renda ou despesa.

O modelo deverá distinguir, quando aplicável:

```text
Entrada real
Saída real
Transferência interna
```

A criação do domínio completo de contas não faz parte automaticamente desta Sprint. Primeiro será definida a regra mínima necessária para que transferências internas não distorçam o fluxo financeiro.

---

## 9. Item 6 — Contrato definitivo de lançamentos externos

**Status: Pendente.**

O contrato da Sprint 02 é provisório e deverá ser revisado após a formalização das regras financeiras.

A revisão deverá tratar especialmente:

- forma de pagamento;
- data da movimentação;
- competência;
- vencimento;
- Crédito;
- transferências internas;
- dados ambíguos ou ausentes.

A fonte externa não deverá inventar ou completar silenciosamente informações financeiras.

---

## 10. Item 7 — Testes das regras financeiras

**Status: Pendente.**

Cada regra formalizada deverá possuir cobertura automatizada antes de alterar o comportamento principal.

Os testes deverão priorizar casos de borda de ciclo, saldo, Crédito, transferências e dados históricos.

---

## 11. Critério de encerramento da Sprint

A Sprint 03 será concluída quando as regras dos sete itens estiverem formalizadas, testadas e implementadas somente onde houver decisão suficiente para isso.

A ordem oficial permanece:

```text
Regra
  ↓
Decisão
  ↓
Documentação
  ↓
Teste
  ↓
Implementação
```

A formalização de um item não implica implementação automática.
