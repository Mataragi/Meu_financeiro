## Financeiro Pro

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

### Problema

Existia a possibilidade de expandir o projeto para um sistema administrativo completo.

### Decisão

O projeto permanecerá focado exclusivamente em finanças pessoais.

### Justificativa

Manter um escopo reduzido aumenta a qualidade do produto e evita funcionalidades desnecessárias.

### Impacto

Todas as novas funcionalidades deverão respeitar esse foco.

---

## DEC-002

### Simplicidade acima da quantidade de funcionalidades.

### Problema

Adicionar muitos recursos pode tornar o sistema complexo.

### Decisão

Priorizar uma interface simples e intuitiva.

### Justificativa

O objetivo do Financeiro Pro é resolver problemas rapidamente, não oferecer dezenas de telas.

### Impacto

Toda nova funcionalidade deverá justificar claramente seu valor.

---

## DEC-003

### Interface Mobile será a principal interface do projeto.

### Problema

A interface Desktop e Mobile evoluíam separadamente.

### Decisão

A evolução do sistema será baseada na experiência Mobile.

### Justificativa

O principal uso do Financeiro Pro ocorre em dispositivos móveis.

### Impacto

A aplicação principal passa a iniciar pela experiência Mobile.

---

## DEC-004

### Ações individuais devem ficar associadas ao registro.

### Problema

Manter botões de edição e exclusão visíveis para todas as transações aumenta a poluição visual e reduz o foco na leitura.

### Decisão

Ações como editar, excluir e duplicar serão exibidas somente quando o registro for expandido.

### Justificativa

A listagem deve priorizar visualização e permitir ações sob demanda.

### Impacto

A interface Mobile utiliza registros expansíveis como menu contextual.

---

# 4. Decisões de Arquitetura

---

## DEC-005

### A tabela "transacoes" será a única fonte de dados financeiros.

### Problema

Duplicação de informações entre módulos.

### Decisão

Centralizar o fluxo financeiro na tabela `transacoes`.

### Justificativa

Evita inconsistências e reduz complexidade.

### Impacto

Todos os módulos financeiros utilizarão essa tabela como base.

---

## DEC-006

### Fluxo financeiro e patrimônio serão separados.

### Problema

Investimentos e transferências distorcem relatórios financeiros quando tratados como despesas.

### Decisão

Criar um domínio específico para patrimônio.

### Justificativa

Fluxo financeiro e patrimônio representam conceitos diferentes.

### Impacto

O módulo Patrimônio será implementado futuramente sem alterar a lógica das transações.

---

## DEC-007

### Parcelamentos serão compostos por transações independentes.

### Problema

Era necessário controlar cada parcela individualmente.

### Decisão

Cada parcela será armazenada como uma transação própria.

### Justificativa

Permite baixa, edição, filtros e exclusão individual.

### Impacto

Maior flexibilidade para consultas e relatórios.

---

## DEC-008

### Fontes externas devem reutilizar o fluxo oficial de transações.

### Problema

Uma integração externa poderia criar uma segunda forma de persistência e duplicar regras de negócio.

### Decisão

O registrador de transações externas deve delegar a persistência ao `transaction_service`, sem acesso direto ao banco.

### Justificativa

Mantém uma única regra de persistência e reduz divergências entre lançamentos manuais e externos.

### Impacto

Novas fontes de dados devem convergir para o fluxo oficial do Financeiro Pro.

---

# 5. Decisões Técnicas

---

## DEC-009

### Utilização do Supabase como banco de dados.

### Problema

Era necessário substituir o armazenamento local.

### Decisão

Migrar para o Supabase.

### Justificativa

Persistência confiável, escalabilidade e simplicidade de integração.

### Impacto

Todos os dados passam a ser centralizados em um banco remoto.

---

## DEC-010

### Organização modular do projeto.

### Problema

O crescimento do código dificultava manutenção.

### Decisão

Separar responsabilidades em módulos.

### Estrutura

- components
- services
- utils

### Impacto

Maior organização e facilidade de evolução.

---

## DEC-011

### Documentação como parte do desenvolvimento.

### Problema

Decisões importantes eram registradas apenas em conversas.

### Decisão

Documentar arquitetura, funcionalidades e decisões do projeto.

### Justificativa

Garantir continuidade e facilitar futuras evoluções.

### Impacto

Toda mudança relevante deverá atualizar a documentação.

---

## DEC-012

### A IA será interpretadora, não autoridade financeira.

### Problema

Uma integração com IA poderia preencher ou alterar informações sem uma regra determinística do sistema.

### Decisão

A IA poderá interpretar uma fonte externa e montar dados estruturados, mas o Financeiro Pro será responsável por validar as regras, detectar inconsistências, verificar duplicidade e executar o lançamento oficial.

### Justificativa

Preserva a confiabilidade dos dados e impede que uma interpretação externa altere silenciosamente a semântica financeira do sistema.

### Impacto

O fluxo futuro seguirá o princípio:

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

### Problema

O sistema vinha utilizando valores como `Cartão de crédito` dentro de categoria para identificar compras realizadas no crédito. Isso mistura o motivo do gasto com o meio utilizado para pagamento e dificulta filtros, somatórios e automações.

### Decisão

A categoria responderá **o que foi gasto ou recebido**, enquanto `forma_pagamento` responderá **como a movimentação foi paga ou recebida**.

As formas de pagamento previstas são:

- PIX
- Débito
- Crédito
- Dinheiro
- Outro

A implementação inicial seguirá o **Plano A**: adicionar `forma_pagamento` sem migração destrutiva do histórico existente.

A migração dos registros históricos será tratada posteriormente pelo **Plano C**, preservando a categoria original sempre que ela puder ser identificada com segurança e sem inventar informação ausente.

### Justificativa

A separação permite, por exemplo, registrar `Combustível` como categoria e `Crédito` como forma de pagamento. Também permite localizar e somar todas as compras feitas no crédito sem transformar o método de pagamento em uma categoria financeira.

### Impacto

Novos lançamentos deverão separar categoria e forma de pagamento. Registros históricos poderão permanecer sem `forma_pagamento` até a migração planejada.

---

## DEC-014

### Compras no crédito começam como pendentes e tornam-se pagas quando a fatura é paga.

### Problema

No cartão de crédito, a compra acontece em uma data, mas o dinheiro somente sai quando a fatura é paga. Tratar a compra como uma saída já paga distorce o controle de caixa utilizado pelo usuário.

### Decisão

Toda compra registrada como `Crédito` deverá iniciar com status `Pendente`. Ela permanecerá pendente até que a fatura correspondente seja efetivamente paga. Após o pagamento da fatura, a transação poderá ser marcada como `Pago` por meio do fluxo oficial de baixa.

A compra no Crédito pertence ao ciclo em que a fatura será paga, mantendo separado o fato de que a compra ocorreu anteriormente.

Exemplo confirmado pelo usuário:

```text
Compra de combustível
R$ 154,66
Forma de pagamento: Crédito

Compra realizada: setembro
Fatura paga: outubro
Vencimento: dia 5

→ lançamento financeiro no ciclo de outubro
→ status inicial: Pendente
→ após pagamento da fatura: Pago
```

A modelagem definitiva da data da compra ainda será definida antes da alteração do banco.

### Justificativa

Essa regra representa o comportamento financeiro real utilizado pelo usuário: a compra cria uma obrigação futura, enquanto o pagamento da fatura representa a saída efetiva do dinheiro.

### Impacto

O contrato de transações deverá distinguir forma de pagamento, data da movimentação, competência/ciclo e vencimento. A automação externa deverá solicitar informações ausentes em operações de crédito, em vez de inventar o ciclo da fatura ou marcar a compra como paga sem evidência de pagamento.

---

## DEC-015

### A ponte ChatGPT → Financeiro Pro será uma porta fina sobre o registrador oficial.

### Problema

A integração com o ChatGPT precisa receber dados interpretados sem criar um segundo caminho de persistência ou permitir que a IA acesse diretamente o banco.

### Decisão

Criar `services/chatgpt_bridge.py` como ponto de entrada para payloads estruturados produzidos pelo ChatGPT. A função `receber_payload_chatgpt()` delegará integralmente ao `external_transaction_service`.

A ponte não realizará chamadas de rede, não acessará Supabase diretamente, não duplicará regras financeiras e não substituirá a confirmação do usuário.

### Justificativa

Uma porta explícita permite conectar posteriormente um mecanismo real de transporte sem alterar o domínio financeiro. A validação, normalização, deduplicação e persistência continuam centralizadas no fluxo oficial.

### Impacto

O Item 3 da Sprint 02 fica implementado sem introduzir API pública, webhook, Edge Function ou processamento automático. Esses mecanismos poderão ser avaliados posteriormente quando houver necessidade real.

---

# 6. Decisões Futuras

Algumas decisões ainda dependem da evolução do projeto.

Entre elas:

- Flutter como próxima plataforma de interface;
- Multiusuário;
- API pública;
- Open Finance;
- Inteligência Artificial como integração operacional;
- modelagem definitiva do campo de data da movimentação;
- regra completa de fechamento e transporte de saldo entre ciclos;
- contas e transferências entre contas próprias;
- contrato definitivo de fontes externas;
- migração histórica da forma de pagamento.

Essas decisões serão registradas quando forem oficialmente aprovadas.

---

# 7. Processo para novas decisões

Sempre que uma decisão impactar:

- arquitetura;
- banco de dados;
- experiência do usuário;
- regras de negócio;
- organização do projeto;

ela deverá ser registrada neste documento.

---

# 8. Princípios

As decisões do Financeiro Pro devem seguir os seguintes princípios:

- Simplicidade.
- Clareza.
- Escalabilidade.
- Manutenibilidade.
- Baixo acoplamento.
- Alto reaproveitamento.

---

# 9. Considerações Finais

O objetivo deste documento não é impedir mudanças.

Seu objetivo é garantir que toda mudança importante seja consciente, registrada e compreendida.

Toda decisão poderá ser revisada no futuro.

Entretanto, nenhuma decisão relevante deverá existir sem uma justificativa documentada.
