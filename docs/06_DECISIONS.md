# Financeiro Pro

# Decisions Log

**Versão do Documento:** 1.0

**Compatível com:** Financeiro Pro v0.9.x

**Status:** Documento Vivo

**Última atualização:** Setembro de 2026

---

# 1. Objetivo

Este documento registra as principais decisões tomadas durante o desenvolvimento do Financeiro Pro.

Seu propósito é preservar o contexto por trás de cada escolha importante.

Ao invés de apenas registrar **o que foi feito**, este documento explica **por que foi feito**.

Essa prática reduz retrabalho, evita decisões contraditórias e facilita a evolução do projeto.

---

# 2. Como utilizar este documento

Toda decisão relevante deve responder às seguintes perguntas:

- Qual problema existia?
- Quais alternativas foram avaliadas?
- Qual decisão foi tomada?
- Qual foi a justificativa?
- Quais impactos essa decisão possui?

---

# 3. Decisões de Produto

---

## DEC-001
### O Financeiro Pro será um aplicativo de finanças pessoais.

O projeto permanecerá focado exclusivamente em finanças pessoais. Manter o escopo reduzido aumenta a qualidade do produto e evita funcionalidades desnecessárias.

---

## DEC-002
### Simplicidade acima da quantidade de funcionalidades.

Toda nova funcionalidade deverá justificar claramente seu valor. O objetivo é resolver problemas rapidamente, sem transformar o produto em um sistema excessivamente complexo.

---

## DEC-003
### Interface Mobile será a principal interface do projeto.

A evolução do sistema será baseada na experiência Mobile, que é a principal forma de uso do Financeiro Pro.

---

## DEC-004
### Ações individuais devem ficar associadas ao registro.

Editar, excluir e duplicar ficam associadas ao registro expandido, reduzindo poluição visual e mantendo a listagem focada na leitura.

---

# 4. Decisões de Arquitetura

---

## DEC-005
### A tabela `transacoes` será a única fonte de dados financeiros.

O fluxo financeiro será centralizado em `transacoes` para evitar duplicação e inconsistência.

---

## DEC-006
### Fluxo financeiro e patrimônio serão separados.

Investimentos e transferências não deverão distorcer relatórios financeiros tratados como despesas. Um domínio específico de patrimônio será criado futuramente.

---

## DEC-007
### Parcelamentos serão compostos por transações independentes.

Cada parcela será uma transação própria, permitindo baixa, edição, filtros e exclusão individual.

---

## DEC-008
### Fontes externas devem reutilizar o fluxo oficial de transações.

O registrador externo delega a persistência ao `transaction_service`, sem acesso direto ao banco, para manter uma única regra oficial de persistência.

---

# 5. Decisões Técnicas

---

## DEC-009
### Utilização do Supabase como banco de dados.

O Supabase foi adotado como persistência centralizada do projeto.

---

## DEC-010
### Organização modular do projeto.

As responsabilidades são separadas principalmente em `components`, `services` e `utils`, favorecendo manutenção e evolução.

---

## DEC-011
### Documentação como parte do desenvolvimento.

Decisões relevantes devem ser documentadas para preservar contexto, reduzir retrabalho e facilitar futuras evoluções.

---

## DEC-012
### A IA será interpretadora, não autoridade financeira.

A IA pode interpretar fontes externas e montar dados estruturados, mas o Financeiro Pro valida regras, detecta inconsistências, verifica duplicidade e executa o lançamento oficial.

Fluxo:

```text
IA interpreta
    ↓
Financeiro Pro valida
    ↓
Usuário confirma
    ↓
Financeiro Pro registra
```

---

## DEC-013
### Categoria e forma de pagamento representam conceitos diferentes.

A categoria responde **o que foi gasto ou recebido**. `forma_pagamento` responde **como a movimentação foi paga ou recebida**.

Formas previstas:

- PIX
- Débito
- Crédito
- Dinheiro
- Outro

A implementação inicial segue o Plano A, sem migração destrutiva. A migração histórica seguirá o Plano C quando houver informação suficiente para preservar a categoria corretamente.

---

## DEC-014
### Compras no crédito começam como pendentes e tornam-se pagas quando a fatura é paga.

Toda compra com `Crédito` inicia como `Pendente` e somente passa a `Pago` após o pagamento da fatura pelo fluxo oficial.

Enquanto estiver pendente, a compra não reduz o saldo real, mas compõe a projeção de saída do ciclo da fatura.

Exemplo:

```text
Compra realizada: 09/09/2026
Fatura: outubro/2026
Vencimento: dia 5

→ data_transacao: 09/09/2026
→ competência: OUTUBRO/2026
→ forma_pagamento: Crédito
→ status inicial: Pendente
→ após pagamento da fatura: Pago
```

---

## DEC-015
### A ponte ChatGPT → Financeiro Pro será uma porta fina sobre o registrador oficial.

`services/chatgpt_bridge.py` recebe payloads estruturados, prepara a proposta e somente persiste após confirmação explícita. Não acessa Supabase diretamente, não duplica regras financeiras e não permite confirmação implícita.

---

## DEC-016
### Data da movimentação, competência e vencimento são conceitos independentes.

```text
quando aconteceu?       → data_transacao
qual ciclo/competência? → mes + ano
quando vence?           → vencimento
quando foi criado?      → criado_em
```

`data_transacao` não deve ser substituída por `criado_em`. `mes` + `ano` não precisam coincidir com o mês civil de `data_transacao`.

Exemplo:

```text
31/08/2026 → data_transacao
SETEMBRO/2026 → mes + ano
```

---

## DEC-017
### O ciclo financeiro é determinado pelos recebimentos principais reais.

Um ciclo começa no dia em que o recebimento principal ocorre e termina no dia anterior ao próximo recebimento principal.

Exemplo:

```text
Recebimento: 30/08/2026
Próximo:     30/09/2026

Ciclo de SETEMBRO/2026:
30/08/2026 → 29/09/2026
```

O dia do recebimento inicia o novo ciclo. A regra acompanha as datas reais dos recebimentos e não depende de o mês ter 28, 29, 30 ou 31 dias.

---

## DEC-018
### Saldo de abertura, saldo real, saldo projetado e saldo transportado são conceitos distintos de transações.

### Problema

O cálculo atual não possui saldo de abertura, encerramento ou transporte formal e trata Entradas Pendentes como entradas já realizadas, enquanto Saídas Pendentes não reduzem o saldo atual. Isso mistura dinheiro efetivamente movimentado com valores previstos.

### Decisão

O modelo oficial passa a ser:

```text
Saldo real =
    saldo de abertura
    + Entradas Pagas
    - Saídas Pagas
```

```text
Saldo projetado =
    saldo real
    - Saídas Pendentes
    + Entradas Pendentes
```

O saldo de encerramento real é o saldo real do ciclo.

O saldo transportado do ciclo N é o saldo de encerramento real do ciclo N e será utilizado como saldo de abertura do ciclo N+1.

```text
Ciclo N
saldo de encerramento
        ↓
Ciclo N+1
saldo de abertura
```

O transporte é uma relação entre ciclos e **não uma nova movimentação financeira**.

### Saldo inicial

No primeiro ciclo controlado pelo Financeiro Pro, o saldo de abertura será informado e confirmado pelo usuário. Ele não será falsificado como uma entrada em `transacoes`.

A representação persistente deverá ser própria para posição de abertura, separada dos fatos financeiros. A forma física dessa representação será definida durante a implementação.

### Fechamento

`Fechamento` não será tratado como tipo financeiro nem como mecanismo de transporte. O encerramento será resultado calculado do ciclo.

Registros históricos eventualmente chamados `Fechamento` não serão apagados ou convertidos automaticamente. Eles deverão ser auditados antes de qualquer migração.

### Alterações retroativas

Como o saldo transportado é derivado do encerramento anterior, uma alteração retroativa que afete um ciclo deverá permitir recalcular os ciclos posteriores. O sistema não deverá depender de saldos de abertura digitados de forma independente para cada ciclo.

### Saldo projetado

A primeira implementação da projeção ficará restrita ao ciclo/horizonte explicitamente consultado. Uma projeção multi-ciclo será tratada como evolução futura.

### Justificativa

Separar fatos financeiros de posições de abertura e resultados de ciclo evita transações artificiais, duplicidade de saldo e distorções de relatórios. Também prepara o domínio para futura evolução da interface para Flutter.

### Impacto

A implementação futura poderá exigir uma representação própria para saldo inicial, identificação formal dos ciclos e recálculo de ciclos dependentes. O cálculo atual permanecerá compatível até que a nova regra seja implementada e coberta por testes.

---

## DEC-019
### O fechamento do Crédito ocorre antes do dia 05, e o dia 05 já pertence à próxima fatura.

### Decisão

A competência da primeira parcela de uma compra no Crédito será determinada pela data real da compra:

```text
Dia 01 a 04
→ primeira parcela na competência do próprio mês

Dia 05 em diante
→ primeira parcela na competência do mês seguinte
```

Exemplos:

```text
04/09/2026 → primeira parcela em SETEMBRO
05/09/2026 → primeira parcela em OUTUBRO
09/09/2026 → primeira parcela em OUTUBRO
```

Em compras parceladas, as parcelas seguintes avançam uma competência por vez.

Exemplo:

```text
Compra em 09/09/2026 em 3x

1ª → OUTUBRO
2ª → NOVEMBRO
3ª → DEZEMBRO
```

### Justificativa

A regra representa o comportamento real da fatura utilizada pelo usuário e permite determinar a competência sem alterar a data real da compra.

---

## DEC-020
### A fatura será inicialmente um agrupamento lógico de lançamentos de Crédito.

Na primeira implementação, não será criada uma tabela física específica de `faturas`.

Uma fatura será representada logicamente pelos lançamentos que atendem:

```text
tipo = Saída
forma_pagamento = Crédito
mes + ano = competência da fatura
```

Para a ação de pagamento, somente registros `Pendente` serão liquidados.

A criação futura de uma entidade física de fatura dependerá de uma necessidade real que não possa ser resolvida pelo modelo atual.

---

## DEC-021
### `Pagar Fatura` será uma ação em lote que liquida os lançamentos de Crédito pendentes da competência selecionada.

A ação deverá localizar:

```text
tipo = Saída
forma_pagamento = Crédito
status = Pendente
mes + ano = competência da fatura
```

Antes da execução, o usuário deverá confirmar a quantidade de lançamentos e o valor total.

Após a confirmação:

```text
Pendente → Pago
```

Nenhum lançamento será apagado, consolidado ou transformado em outro tipo de transação.

As ações individuais dos cards continuam disponíveis para editar, excluir, duplicar e dar baixa quando necessário.

### Impacto no saldo

Antes do pagamento:

```text
Saldo real → não é reduzido
Saldo projetado → considera a saída pendente
```

Após o pagamento:

```text
Saída passa a ser Paga
        ↓
compor o saldo real
```

### Justificativa

A baixa em lote reproduz a operação real de pagamento da fatura e elimina a necessidade de selecionar manualmente cada parcela ou compra de Crédito.

---

## DEC-022
### Transferências entre contas do casal usadas apenas como rota de pagamento não serão registradas como movimentações financeiras.

Quando uma transferência entre contas próprias ocorrer apenas para viabilizar o pagamento de uma compra, o Financeiro Pro deverá registrar somente a compra real.

Exemplo:

```text
Sua conta
   ↓ transferência
Conta da esposa
   ↓ PIX
Compra X
```

O registro financeiro será somente:

```text
Descrição: Compra X
Valor: R$ X
Tipo: Saída
Forma de pagamento: PIX
```

A transferência intermediária não será tratada como Entrada, Saída ou nova despesa.

### Justificativa

A transferência altera apenas a rota utilizada para executar uma despesa que já ocorreu. Registrá-la criaria duplicidade e distorceria o saldo e os relatórios.

### Limite

Não será criado nesta Sprint um domínio completo de contas bancárias, contas do casal ou transferências internas apenas para representar esse comportamento.

---

## DEC-023
### Movimentações entre a conta familiar e a corretora não são receita nem despesa.

Valores enviados da conta familiar para a corretora representam movimentação patrimonial/investimento, e não uma despesa.

Valores retornados da corretora para a conta familiar representam retorno de patrimônio, e não uma nova receita, quando forem apenas a devolução de dinheiro já pertencente à família.

Exemplo:

```text
Conta familiar → Corretora
R$ 3.000

→ não é despesa
```

```text
Corretora → Conta familiar
R$ 3.000

→ não é receita
```

O mesmo valor não poderá ser contabilizado simultaneamente como saída e entrada do fluxo financeiro apenas por ter mudado de localização patrimonial.

### Justificativa

Receitas e despesas devem representar geração ou consumo de recursos no fluxo financeiro. Transferências para a corretora alteram a posição patrimonial, mas não representam consumo de recursos da família.

### Limite

O controle detalhado de patrimônio, posições, investimentos e contas/corretoras permanece como evolução futura. Esta decisão apenas impede que essas movimentações distorçam o fluxo financeiro atual.

---

## DEC-024
### A nomenclatura financeira oficial passa a usar `Receita` e `Despesa`.

Os conceitos anteriormente apresentados na interface e em parte do código como `Entrada` e `Saída` passam a ser denominados oficialmente:

```text
Entrada → Receita
Saída   → Despesa
```

A semântica permanece:

```text
Receita = dinheiro que entra no patrimônio familiar vindo de fora
Despesa = dinheiro efetivamente gasto
```

### Categoria e forma de pagamento

A categoria representa a **finalidade econômica** da movimentação. A forma de pagamento representa **como a movimentação foi paga ou recebida**.

Categorias oficiais:

- Moradia
- Utilidades
- Mercado
- Alimentação
- Transporte
- Saúde
- Educação
- Família
- Lazer & Presentes
- Cuidados pessoais
- Dívidas
- Outros
- Sem categoria

Formas de pagamento:

- PIX
- Débito
- Crédito
- Dinheiro
- Outro

`Cartão Crédito Luiz` não deverá permanecer como categoria. Informação de cartão pertence ao conceito de forma de pagamento.

### Contrato de lançamentos externos

O contrato externo definitivo deverá separar os seguintes campos:

```text
descricao
valor
tipo
status
categoria
forma_pagamento
data_transacao
mes
ano
vencimento
```

Para o contrato oficial:

- `tipo` utiliza `Receita` ou `Despesa`;
- `status` utiliza `Pago` ou `Pendente`;
- `mes` + `ano` representam a competência/ciclo financeiro;
- `data_transacao` representa a data real da operação;
- `vencimento` é opcional quando não existe obrigação futura;
- `categoria` não deve carregar a informação de forma de pagamento;
- dados ausentes ou ambíguos não devem ser inventados pela fonte externa.

Quando a transação for uma compra no `Crédito`, o lançamento deverá respeitar as regras da DEC-014 e DEC-019.

### Justificativa

A nova nomenclatura melhora a linguagem da futura interface e torna o domínio mais claro. A separação entre categoria e forma de pagamento evita categorias híbridas e prepara relatórios, filtros, gráficos e automações confiáveis.

### Impacto

A alteração de nomenclatura não autoriza migração histórica automática. Registros existentes com `Entrada`, `Saída`, `Cartão Crédito Luiz`, `Contas` ou outras classificações antigas deverão ser auditados antes de qualquer migração.

A mudança de código e banco será realizada de forma incremental, preservando compatibilidade durante a transição.

---

# 6. Decisões Futuras

Algumas decisões ainda dependem da evolução do projeto:

- Flutter como próxima plataforma de interface;
- Multiusuário;
- API pública;
- Open Finance;
- Inteligência Artificial como integração operacional;
- identificação física dos ciclos no banco;
- persistência definitiva do saldo de abertura;
- política de auditoria para registros históricos de `Fechamento`;
- comportamento de alterações retroativas entre ciclos;
- contas e transferências entre contas próprias;
- migração histórica da forma de pagamento;
- múltiplos cartões, caso essa necessidade seja incorporada ao domínio futuramente.

Essas decisões serão registradas quando forem oficialmente aprovadas.

---

# 7. Processo para novas decisões

Sempre que uma decisão impactar arquitetura, banco de dados, experiência do usuário, regras de negócio ou organização do projeto, ela deverá ser registrada neste documento.

---

# 8. Princípios

As decisões do Financeiro Pro devem seguir:

- Simplicidade.
- Clareza.
- Escalabilidade.
- Manutenibilidade.
- Baixo acoplamento.
- Alto reaproveitamento.

---

# 9. Considerações Finais

O objetivo deste documento não é impedir mudanças. É garantir que toda mudança importante seja consciente, registrada e compreendida.
