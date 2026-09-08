# Financeiro Pro

# Sprint 02 — Automação de Lançamentos

**Status:** Em desenvolvimento

**Objetivo:** preparar o Financeiro Pro para receber movimentações de fontes externas, especialmente comprovantes interpretados por IA, sem comprometer a confiabilidade dos dados financeiros.

---

## 1. Princípio central

O Financeiro Pro permanece responsável pela regra financeira.

A IA pode interpretar uma fonte externa e propor dados estruturados, mas não deve inventar informações nem decidir silenciosamente regras que pertençam ao sistema.

Fluxo desejado:

```text
Comprovante / fonte externa
        ↓
Interpretação
        ↓
Payload estruturado
        ↓
Validação do Financeiro Pro
        ↓
Duplicidade
        ↓
Confirmação do usuário
        ↓
Transaction Service
        ↓
Repository
        ↓
Supabase
```

---

## 2. Itens da Sprint

| Item | Tarefa | Status |
|---|---|---|
| 1 | Criar registrador de transações externas | ✅ Concluído |
| 2 | Definir contrato e regras de entrada | 🔄 Em definição |
| 3 | Criar porta de integração ChatGPT → Financeiro Pro | ✅ Concluído |
| 4 | Implementar confirmação antes do lançamento | ⏳ Pendente |
| 5 | Validar fluxo ponta a ponta | ⏳ Pendente |

---

## 3. Item 1 — Registrador de transações externas

Implementado em `services/external_transaction_service.py`.

Responsabilidades atuais:

- receber dados estruturados;
- validar campos mínimos;
- normalizar status;
- rejeitar duplicidades segundo a regra atual;
- reutilizar `transaction_service` para persistência;
- não acessar Supabase diretamente;
- não depender de Streamlit.

O registrador não interpreta comprovantes e não define regras de competência financeira.

---

## 4. Item 3 — Porta de integração ChatGPT → Financeiro Pro

Implementada em `services/chatgpt_bridge.py`.

A função pública `receber_payload_chatgpt()` representa a porta de entrada para payloads produzidos pelo ChatGPT.

Responsabilidades da porta:

- receber um payload estruturado;
- encaminhar o payload ao registrador oficial;
- preservar o resultado do registrador;
- não acessar Supabase diretamente;
- não realizar chamadas de rede;
- não duplicar validações ou regras financeiras;
- não executar confirmação automática do usuário.

Fluxo atual:

```text
ChatGPT
   ↓
receber_payload_chatgpt()
   ↓
external_transaction_service
   ↓
transaction_service
   ↓
Repository
   ↓
Supabase
```

A porta é deliberadamente fina. A existência de uma função específica permite conectar posteriormente um mecanismo real de transporte sem alterar o domínio financeiro.

A implementação atual não cria API pública, webhook, Edge Function ou processamento automático. Esses recursos permanecem fora do escopo desta etapa.

---

## 5. Contrato provisório de entrada

Campos mínimos atuais do registrador externo:

- `descricao`
- `valor`
- `tipo`
- `status`
- `mes`
- `ano`
- `categoria`
- `vencimento`
- `forma_pagamento`
- `data_transacao`

Formato esperado de data: `YYYY-MM-DD` no payload estruturado. A interface pode apresentar a data em formato brasileiro, mas a integração utiliza o valor de data normalizado pelo serviço.

O contrato será refinado conforme as regras financeiras restantes forem formalizadas. A porta ChatGPT não deve interpretar ou preencher silenciosamente campos cuja informação não esteja disponível.

---

## 6. Regras já confirmadas

### Status

Os únicos estados persistidos são:

- `Pago`
- `Pendente`

Entradas equivalentes podem ser normalizadas antes da persistência.

Para compras com `forma_pagamento = Crédito`, o status inicial será obrigatoriamente `Pendente`. Após o pagamento da fatura correspondente, a transação poderá ser marcada como `Pago` pelo fluxo oficial de baixa.

### Tipo

Os tipos utilizados no fluxo principal são:

- `Entrada`
- `Saída`

### Categoria x forma de pagamento

A categoria representa **o que foi gasto ou recebido**.

A forma de pagamento representa **como a movimentação foi paga ou recebida**.

Formas previstas:

- `PIX`
- `Débito`
- `Crédito`
- `Dinheiro`
- `Outro`

A implementação inicial seguirá o **Plano A**: adicionar `forma_pagamento` sem migração destrutiva do histórico.

A migração dos registros históricos seguirá posteriormente o **Plano C**, preservando a categoria original quando identificável com segurança e sem inventar dados ausentes.

### Competência mensal

O sistema trabalha com `mes` e `ano` como referência explícita da competência do lançamento.

Parcelamentos já possuem regra de avanço de mês e ano.

### Parcelamentos

Cada parcela é uma transação independente e compartilha um identificador de grupo.

---

## 7. Regra financeira do ciclo

O usuário confirmou que o ciclo financeiro pessoal utilizado pelo Financeiro Pro considera o recebimento no dia 30.

Por isso, movimentações realizadas nos dias 30 e 31 podem pertencer ao ciclo financeiro do mês seguinte.

Exemplo confirmado:

```text
31/08/2026
    ↓
Ciclo financeiro de SETEMBRO/2026
```

Essa regra ainda não foi implementada automaticamente no código.

---

## 8. Regra de pagamento no crédito

Compras realizadas no Crédito não devem ser tratadas como saída de caixa já paga no momento da compra, porque o dinheiro será comprometido quando a fatura for paga.

Para pagamentos imediatos, como PIX, Débito e Dinheiro, o ciclo financeiro será determinado pela data da movimentação segundo a regra de fechamento do ciclo.

Para Crédito, o lançamento financeiro deverá pertencer ao ciclo em que a fatura será paga, mantendo separado o fato de que a compra ocorreu anteriormente.

O status inicial de uma compra no Crédito é `Pendente`. Quando a fatura correspondente for paga, o lançamento poderá ser baixado para `Pago` pelo fluxo oficial.

Exemplo confirmado:

```text
Compra de combustível
R$ 154,66
Forma de pagamento: Crédito

Compra realizada: setembro
Fatura: outubro
Vencimento: dia 5

→ lançamento financeiro no ciclo de outubro
→ status inicial: Pendente
→ após pagamento da fatura: Pago
```

A modelagem definitiva da data da compra ainda não foi implementada e deverá ser definida antes da alteração estrutural do banco.

Quando uma operação de Crédito não possuir informação suficiente para determinar o ciclo da fatura, a automação deverá solicitar complemento ou confirmação.

---

## 9. Pontos que não devem ser inventados

A automação não deve deduzir silenciosamente:

- competência a partir de uma data sem regra definida;
- ciclo da fatura de Crédito sem informação suficiente;
- vencimento a partir da data do comprovante;
- categoria quando houver ambiguidade;
- forma de pagamento quando não houver evidência suficiente;
- conta de origem ou destino que não exista no contrato;
- identificador externo inexistente;
- natureza financeira de uma transferência entre contas próprias;
- status `Pago` para uma compra no Crédito sem evidência de pagamento da fatura.

Quando uma informação necessária estiver ausente ou ambígua, o fluxo deverá solicitar confirmação ou complemento.

---

## 10. Duplicidade

A proteção atual do registrador externo utiliza comparação determinística dos dados recebidos.

Essa abordagem é adequada como primeira barreira, mas não deve ser considerada uma identificação definitiva da operação bancária.

Evolução futura poderá incorporar identificador externo, referência do comprovante ou outra evidência única da operação.

---

## 11. Fora do escopo desta etapa

Não fazem parte da implementação atual:

- upload de comprovantes dentro do app;
- webhook público;
- API pública;
- Edge Function;
- fila de processamento;
- banco auxiliar;
- autenticação adicional;
- processamento automático sem confirmação;
- alteração do cálculo de saldo;
- criação de contas bancárias como novo domínio;
- migração destrutiva do histórico para `forma_pagamento`.

Esses recursos somente serão considerados quando houver necessidade real e contrato definido.

---

## 12. Próximas decisões obrigatórias

Antes da automação completa, devem ser definidas:

1. campo e semântica definitivos da data da movimentação;
2. diferença operacional entre data da movimentação, competência/ciclo e vencimento;
3. regra completa do ciclo financeiro;
4. comportamento de entradas e saídas realizadas em dias de fechamento do ciclo;
5. tratamento de transferências entre contas próprias;
6. obrigatoriedade e catálogo de categorias;
7. contrato definitivo para fontes externas, incluindo `forma_pagamento`;
8. estratégia de confirmação do usuário;
9. estratégia de deduplicação futura;
10. comportamento para dados incompletos ou ambíguos;
11. estratégia de migração histórica da forma de pagamento.

---

## 13. Critério de conclusão da Sprint

A Sprint 02 somente será considerada concluída quando uma fonte externa puder:

```text
ser interpretada
    ↓
ser convertida em dados estruturados
    ↓
ser validada pelas regras do Financeiro Pro
    ↓
ser apresentada para confirmação
    ↓
ser registrada pelo fluxo oficial de transações
```

sem duplicar regras, acessar o banco diretamente ou alterar silenciosamente a semântica financeira do sistema.
