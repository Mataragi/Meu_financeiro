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
| 3 | Criar porta de integração ChatGPT → Financeiro Pro | ⏳ Pendente |
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

## 4. Contrato provisório de entrada

Campos mínimos atuais do registrador externo:

- `descricao`
- `valor`
- `tipo`
- `status`
- `mes`
- `ano`
- `categoria`
- `vencimento`

Esses campos representam o contrato técnico atual, mas algumas regras de negócio ainda precisam ser formalizadas antes da automação completa.

---

## 5. Regras já confirmadas

### Status

Os únicos estados persistidos são:

- `Pago`
- `Pendente`

Entradas equivalentes podem ser normalizadas antes da persistência.

### Tipo

Os tipos utilizados no fluxo principal são:

- `Entrada`
- `Saída`

### Competência mensal

O sistema trabalha com `mes` e `ano` como referência explícita da competência do lançamento.

Parcelamentos já possuem regra de avanço de mês e ano.

### Parcelamentos

Cada parcela é uma transação independente e compartilha um identificador de grupo.

---

## 6. Regra financeira em definição

O usuário confirmou que o ciclo financeiro pessoal utilizado pelo Financeiro Pro considera o recebimento no dia 30.

Por isso, movimentações realizadas nos dias 30 e 31 podem pertencer ao ciclo financeiro do mês seguinte.

Exemplo confirmado:

```text
31/08/2026
    ↓
Ciclo financeiro de SETEMBRO/2026
```

Essa regra ainda não foi implementada no código e deverá ser formalizada antes de ser usada automaticamente pelo registrador externo.

---

## 7. Pontos que não devem ser inventados

A automação não deve deduzir silenciosamente:

- competência a partir de uma data sem regra definida;
- vencimento a partir da data do comprovante;
- categoria quando houver ambiguidade;
- conta de origem ou destino que não exista no contrato;
- identificador externo inexistente;
- natureza financeira de uma transferência entre contas próprias.

Quando uma informação necessária estiver ausente ou ambígua, o fluxo deverá solicitar confirmação ou complemento.

---

## 8. Duplicidade

A proteção atual do registrador externo utiliza comparação determinística dos dados recebidos.

Essa abordagem é adequada como primeira barreira, mas não deve ser considerada uma identificação definitiva da operação bancária.

Evolução futura poderá incorporar identificador externo, referência do comprovante ou outra evidência única da operação.

---

## 9. Fora do escopo desta etapa

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
- criação de contas bancárias como novo domínio.

Esses recursos somente serão considerados quando houver necessidade real e contrato definido.

---

## 10. Próximas decisões obrigatórias

Antes da integração automática, devem ser definidas:

1. diferença entre data da movimentação, competência e vencimento;
2. regra completa do ciclo financeiro;
3. comportamento de entradas e saídas realizadas em dias de fechamento do ciclo;
4. tratamento de transferências entre contas próprias;
5. obrigatoriedade e catálogo de categorias;
6. contrato definitivo para fontes externas;
7. estratégia de confirmação do usuário;
8. estratégia de deduplicação futura;
9. comportamento para dados incompletos ou ambíguos.

---

## 11. Critério de conclusão da Sprint

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
