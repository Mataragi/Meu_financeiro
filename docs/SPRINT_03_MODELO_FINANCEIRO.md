# Financeiro Pro

# Sprint 03 — Formalização do Modelo Financeiro

**Status:** Em desenvolvimento

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
| 1 | Formalizar data da movimentação, competência e vencimento | 🔴 | ✅ |
| 2 | Formalizar regra completa do ciclo financeiro | 🔴 | ✅ |
| 3 | Definir modelo de saldo real, pendências e saldo transportado | 🔴 | ⏳ |
| 4 | Formalizar comportamento de Crédito e pagamento de fatura | 🔴 | ⏳ |
| 5 | Definir tratamento de transferências entre contas próprias | 🟠 | ⏳ |
| 6 | Formalizar contrato definitivo para lançamentos externos | 🟠 | ⏳ |
| 7 | Criar testes das regras financeiras formalizadas | 🔴 | ⏳ |

---

## 4. Item 1 — Data da movimentação, competência e vencimento

**Status: Concluído.**

### 4.1 Definições oficiais

O modelo financeiro passa a tratar três conceitos diferentes:

**`data_transacao`**

Representa a data em que a operação financeira efetivamente aconteceu.

Ela descreve o fato financeiro e não o momento em que o registro foi criado no sistema.

```text
data_transacao ≠ criado_em
```

`criado_em` continua representando o momento de criação do registro e não deve ser utilizado como substituto da data da operação.

**`mes` + `ano`**

Representam a competência/ciclo financeiro ao qual o lançamento pertence.

Essa competência é uma informação financeira explícita e não deve ser confundida automaticamente com o mês de `data_transacao`.

**`vencimento`**

Representa o dia em que uma obrigação deve ser paga, quando existir uma obrigação com vencimento aplicável.

Portanto, `vencimento` não é a data em que a operação necessariamente aconteceu.

### 4.2 Regra de separação

```text
QUANDO aconteceu?
       ↓
 data_transacao

EM QUAL ciclo financeiro será considerado?
       ↓
 mes + ano

QUANDO a obrigação vence?
       ↓
 vencimento
```

Os três campos possuem semânticas diferentes e não devem ser preenchidos por cópia automática de um para outro sem regra explícita.

### 4.3 Exemplo confirmado

Uma operação realizada em 31/08/2026 pode pertencer ao ciclo financeiro de setembro:

```text
31/08/2026
    ↓
data_transacao

SETEMBRO/2026
    ↓
mes + ano
```

O fato de a operação ter ocorrido em agosto não obriga o lançamento a pertencer à competência de agosto.

### 4.4 Regra para vencimento

O sistema não deve inferir o vencimento simplesmente a partir de `data_transacao`.

Quando não existir informação de vencimento aplicável, o campo deverá permanecer ausente/nulo conforme o contrato do fluxo de entrada.

Quando existir um vencimento conhecido, ele deverá ser registrado como o dia da obrigação correspondente.

Para operações de Crédito, o vencimento está associado à obrigação/fatura e não à data em que a compra foi realizada.

### 4.5 Consequência para automações

Uma fonte externa deverá informar ou permitir confirmar separadamente:

- quando a operação ocorreu;
- em qual competência/ciclo ela deve ser registrada;
- qual é o vencimento, quando houver.

A automação não deverá preencher silenciosamente esses campos usando uma única data como fonte para todos os significados.

### 4.6 Limites desta decisão

Este item não implementa ainda a regra automática que transforma uma `data_transacao` em `mes` + `ano`.

Também não define a regra completa de fechamento do ciclo, pois essa decisão pertence ao Item 2.

O comportamento específico de Crédito e fatura será aprofundado no Item 4.

### 4.7 Critério de aceite do Item 1

Considera-se o Item 1 concluído quando o sistema e sua documentação reconhecem que:

```text
data_transacao = fato ocorrido
mes + ano       = competência/ciclo financeiro
vencimento      = dia da obrigação, quando aplicável
criado_em       = momento de criação do registro
```

Sem utilizar `criado_em` como data financeira e sem assumir que os três conceitos são intercambiáveis.

---

## 5. Item 2 — Ciclo financeiro

**Status: Concluído.**

### 5.1 Regra oficial

O ciclo financeiro é definido pelas **datas reais dos recebimentos principais**.

> **Um ciclo começa no dia em que o recebimento principal ocorre e termina no dia anterior ao próximo recebimento principal.**

O ciclo não é definido pelo primeiro e pelo último dia do mês civil e não depende de o mês possuir 28, 29, 30 ou 31 dias.

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

### 5.2 Exemplo de referência

Considerando recebimentos principais em 30/08/2026 e 30/09/2026:

```text
Ciclo de SETEMBRO/2026

Início: 30/08/2026
Fim:    29/09/2026

Próximo ciclo

Início: 30/09/2026
Fim:    29/10/2026
```

Assim, uma operação realizada em 31/08/2026 pertence ao ciclo de setembro, enquanto uma operação realizada em 29/09/2026 ainda pertence ao mesmo ciclo. A operação realizada em 30/09/2026 pertence ao novo ciclo.

### 5.3 O ciclo acompanha a data real do recebimento

O sistema não deverá assumir que o recebimento sempre acontecerá no dia 30.

Se a data real do recebimento principal mudar, o limite do ciclo também muda.

Exemplo:

```text
Recebimento anterior: 30/08/2026
Próximo recebimento:  29/09/2026

Ciclo:
30/08/2026 → 28/09/2026

Novo ciclo:
29/09/2026 → dia anterior ao próximo recebimento
```

Portanto, a regra é **ancorada nas datas reais dos recebimentos**, e não em um número fixo do calendário.

### 5.4 Regra para o dia do recebimento

O próprio dia do recebimento inicia o novo ciclo.

Logo:

```text
Recebimento em 30/09
        ↓
30/09 pertence ao novo ciclo

29/09
        ↓
último dia do ciclo anterior
```

Isso formaliza a regra prática de que operações dos dias 30 e 31 podem pertencer ao ciclo seguinte quando o próximo recebimento inicia esse ciclo.

### 5.5 Regra para o dia 1

O dia 1 não possui tratamento especial.

Ele pertence ao ciclo que estiver vigente naquela data.

Exemplo:

```text
30/08 → início do ciclo
31/08
01/09
02/09
...
29/09 → fim do ciclo
30/09 → início do próximo ciclo
```

Portanto, o calendário civil não reinicia o ciclo financeiro no dia 1.

### 5.6 Entradas e saídas

A classificação do ciclo é determinada pela **data em que a movimentação financeira ocorre dentro do período do ciclo**, respeitando as regras específicas de competência já definidas para situações como Crédito.

Isso significa que uma entrada ou saída ocorrida entre o início e o fim do ciclo pertence àquele ciclo, salvo quando uma regra financeira específica determinar outra competência.

O ciclo, portanto, não transforma automaticamente toda movimentação em uma simples regra de `mês(data_transacao)`.

### 5.7 Parcelamentos

Parcelamentos continuam sendo compostos por transações independentes.

Cada parcela deverá possuir sua própria competência/ciclo financeiro, de acordo com o período financeiro ao qual aquela parcela pertence.

O calendário civil não deve ser utilizado isoladamente para decidir a competência de uma parcela.

A regra geral é:

```text
Data/obrigação da parcela
        ↓
identificação do ciclo vigente
        ↓
mes + ano da parcela
```

A lógica específica de geração das parcelas permanece no domínio de parcelamentos e deverá ser coberta pelos testes da Sprint 03. Este Item não altera a implementação existente.

### 5.8 Virada de ano

A virada do ano não interrompe artificialmente um ciclo.

Se um ciclo atravessar dezembro e janeiro, ele continua até o dia anterior ao próximo recebimento.

Exemplo:

```text
Recebimento: 30/12/2026
Próximo:     30/01/2027

Ciclo:
30/12/2026 → 29/01/2027
```

Nesse caso, o ciclo possui início em 2026 e termina em 2027. O `mes` + `ano` utilizado pelo lançamento deverá representar o ciclo financeiro ao qual ele pertence, e não simplesmente o mês civil da data da operação.

### 5.9 Limites da decisão

Este Item formaliza **como o período de um ciclo é delimitado**.

Ele não define ainda:

- como o saldo de abertura será calculado;
- como o saldo será transportado para o próximo ciclo;
- como pendências afetarão saldo real ou projetado;
- como uma fatura de Crédito será liquidada.

Esses comportamentos pertencem aos Itens 3 e 4.

Também não implementa ainda a determinação automática do ciclo no código de produção.

### 5.10 Critério de aceite do Item 2

Considera-se o Item 2 concluído quando a regra puder ser expressa sem depender do número de dias do mês:

```text
Ciclo atual:
recebimento principal atual
        ↓
até
um dia antes do próximo recebimento principal
```

E quando estiver claro que:

- o dia do recebimento inicia o novo ciclo;
- o dia anterior ao próximo recebimento encerra o ciclo atual;
- o dia 1 não reinicia o ciclo;
- meses com 28, 29, 30 ou 31 dias não alteram a regra;
- a virada de ano não interrompe o ciclo;
- parcelamentos respeitam o ciclo financeiro de cada parcela;
- regras específicas, como Crédito, podem definir uma competência própria e serão tratadas em seus respectivos itens.

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
