# Financeiro Pro

# Features Documentation

**Versão do Documento:** 1.2

**Compatível com:** Financeiro Pro v0.9.x

**Status:** Documento Vivo

**Última atualização:** Setembro de 2026

---

# 1. Objetivo

Este documento descreve todas as funcionalidades disponíveis no Financeiro Pro.

Seu objetivo é servir como referência funcional do sistema.

Cada funcionalidade é documentada com:

- objetivo;
- funcionamento;
- regras de negócio;
- dependências;
- limitações;
- possibilidades de evolução.

Este documento não descreve implementação técnica.

Essa responsabilidade pertence ao documento **Architecture**.

---

# 2. Organização

O Financeiro Pro está dividido nos seguintes módulos.

```

Financeiro Pro

├── Transações
├── Parcelamentos
├── Dashboard
├── Importação
├── Backup
├── Dívidas Informais
└── Sistema

```

Cada módulo representa um conjunto de funcionalidades relacionadas.

---

# 3. Módulo: Transações

## Status

🟢 Estável

## Objetivo

Permitir registrar toda movimentação financeira do usuário.

As transações representam o fluxo financeiro da aplicação.

São a principal fonte de dados utilizada pelos demais módulos.

---

## Funcionalidades

### Cadastro Manual

Permite registrar:

- Entradas
- Saídas

Campos funcionais atuais:

- descrição
- valor
- categoria
- status
- vencimento
- mês
- ano

Evolução definida para novos lançamentos:

- forma de pagamento

A categoria representa o que foi gasto ou recebido. A forma de pagamento representa como a movimentação foi paga ou recebida.

Formas de pagamento previstas:

- PIX
- Débito
- Crédito
- Dinheiro
- Outro

O histórico existente não sofrerá migração destrutiva. A migração dos registros antigos será tratada posteriormente.

---

### Consulta

Permite visualizar transações utilizando filtros por:

- ano
- mês
- status
- descrição
- forma de pagamento

A interface Mobile apresenta os lançamentos em registros expansíveis, priorizando a visualização e mantendo as ações individuais ocultas até a interação do usuário.

A visualização principal utiliza registros compactos. Uma visualização em tabela permanece disponível como alternativa para conferência e análise de vários lançamentos.

---

### Edição

É possível alterar:

- descrição
- valor
- categoria
- status
- vencimento
- forma de pagamento, quando disponível no registro

A edição mantém o mesmo registro.

Não cria uma nova transação.

No Mobile, a edição é acessada dentro do menu contextual do próprio registro.

---

### Exclusão

Permite excluir:

- uma transação
- múltiplas transações
- um grupo inteiro de parcelamentos

A exclusão individual exige confirmação do usuário.

---

### Duplicação

Permite criar uma nova transação a partir de um registro existente.

A cópia pode ser direcionada para outro mês e ano.

A nova transação é criada como **Pendente**.

A duplicação não reaproveita o identificador do registro original nem o grupo de parcelamento.

---

### Baixa

Permite alterar o status de uma transação para:

Pago

Essa funcionalidade é utilizada para confirmar pagamentos realizados.

A baixa em lote permanece disponível separadamente das ações individuais.

---

### Fontes Externas

O sistema possui um registrador para receber transações em formato estruturado de fontes externas.

O registrador valida os dados recebidos, normaliza o status, protege contra duplicidades segundo a regra atual e reutiliza o fluxo oficial de transações.

Ele não interpreta comprovantes e não define sozinho regras de competência financeira.

---

### Compras no Crédito

Compras feitas no Crédito possuem comportamento financeiro diferente de pagamentos imediatos.

Em pagamentos imediatos, como PIX, Débito e Dinheiro, o ciclo financeiro acompanha a data da movimentação segundo a regra de fechamento do Financeiro Pro.

No Crédito, a compra ocorre antes da saída efetiva do dinheiro. O lançamento financeiro pertence ao ciclo em que a fatura será paga, enquanto a data da compra deverá ser preservada separadamente quando a modelagem definitiva for implementada.

Exemplo:

```text
Compra de combustível
R$ 154,66
Forma de pagamento: Crédito

Compra: setembro
Fatura: outubro
Vencimento: dia 5

→ ciclo financeiro de outubro
```

A automação deverá pedir complemento quando não houver informação suficiente para determinar o ciclo da fatura.

---

## Dependências

- Banco de Dados
- Dashboard
- Timeline (futura)
- Parcelamentos
- Importação

---

## Limitações Atuais

As transações representam apenas fluxo financeiro.

Não representam patrimônio.

A modelagem definitiva da data da movimentação, do fechamento completo do ciclo e do transporte de saldo ainda será evoluída antes de automatizações dependentes dessas regras.

---

# 4. Módulo: Parcelamentos

## Status

🟢 Estável

## Objetivo

Permitir registrar compras parceladas mantendo controle individual de cada parcela.

---

## Funcionamento

Ao criar um parcelamento:

o sistema cria múltiplas transações independentes.

Todas compartilham o mesmo:

```

grupo_parcelamento

```

Cada parcela possui:

- vencimento próprio
- mês próprio
- ano próprio
- status próprio

---

## Benefícios

Essa abordagem permite:

- baixa individual
- exclusão completa
- filtros mensais
- relatórios corretos

---

## Dependências

- Transações

---

## Evolução Planejada

No futuro o parcelamento poderá compartilhar parte da infraestrutura com o módulo de recorrências.

---

# 5. Módulo: Dashboard

## Status

🟢 Estável

## Objetivo

Apresentar um resumo financeiro do período selecionado.

---

## Informações exibidas

- Total pago

- Total pendente

- Saldo

- Lista de transações

---

## Origem dos Dados

Todas as informações são calculadas a partir da tabela:

```

transacoes

```

---

## Evoluções Futuras

- gráficos

- indicadores

- patrimônio

- evolução mensal

---

# 6. Módulo: Importação de Extratos

## Status

🟢 Estável

---

## Objetivo

Reduzir o trabalho manual de cadastro de movimentações.

---

## Funcionamento

O usuário envia um arquivo CSV.

O sistema interpreta o conteúdo.

As movimentações são convertidas em transações.

---

## Benefícios

- velocidade

- redução de erros

- economia de tempo

---

## Limitações

Atualmente depende do layout esperado pelo parser.

---

## Evolução Planejada

Criar um sistema inteligente capaz de reconhecer diferentes layouts bancários.

---

# 7. Módulo: Backup

## Status

🟢 Estável

---

## Objetivo

Garantir que os dados possam ser recuperados.

---

## Funcionalidades

Exportação

↓

CSV

↓

Download

---

Restauração

↓

Upload

↓

Importação

---

## Objetivo Estratégico

Evitar perda de dados.

---

# 8. Módulo: Dívidas Informais

## Status

🟢 Estável

## Objetivo

Registrar valores emprestados entre pessoas.

## Funcionalidades

Cadastro

Consulta

Edição

Exclusão

## Regras

Essas movimentações não fazem parte do fluxo financeiro principal.

São armazenadas em domínio separado.

---

# 9. Interface Mobile

## Status

🟢 Principal

## Objetivo

Oferecer uma experiência rápida para utilização diária.

## Características

- poucos cliques
- filtros rápidos
- cadastro simplificado
- leitura otimizada
- ações contextuais por registro
- ferramentas globais centralizadas
- visualização em cards como padrão
- visualização em tabela como alternativa de análise

## Estrutura de ações

### Ações individuais

Associadas diretamente ao registro:

- Editar
- Excluir
- Duplicar

Essas ações ficam ocultas até a expansão do registro.

### Ações em lote

Mantidas em seção própria:

- Dar baixa
- Excluir registros

### Ferramentas globais

Mantidas em seção própria:

- Backup
- Restaurar backup

## Objetivo de UX

O usuário deve conseguir registrar uma movimentação em poucos segundos e visualizar os lançamentos sem excesso de controles permanentes na tela.

---

# 10. Interface Desktop

## Status

🟡 Descontinuada como interface principal

## Situação Atual

A aplicação principal utiliza a experiência Mobile.

O código histórico do Desktop será removido ou reaproveitado somente quando isso puder ser feito sem risco para funcionalidades compartilhadas.

---

# 11. Funcionalidades Planejadas

As funcionalidades abaixo fazem parte do roadmap do produto.

---

## Timeline

Status

🟡 Planejada

Objetivo

Apresentar o histórico financeiro em formato cronológico.

---

## Recorrências

Status

🟡 Planejada

Objetivo

Automatizar lançamentos recorrentes.

---

## Patrimônio

Status

🟡 Planejada

Objetivo

Separar patrimônio do fluxo financeiro.

Esse módulo permitirá controlar:

- contas

- corretoras

- investimentos

- patrimônio líquido

---

## Login

Status

🟡 Planejada

---

## Multiusuário

Status

🟡 Planejada

---

## Flutter

Status

🟡 Planejada

A migração para Flutter será realizada futuramente como evolução da interface e da experiência mobile. O Streamlit permanece como plataforma atual de validação e uso do produto.

---

# 12. Funcionalidades Descontinuadas

Atualmente nenhuma funcionalidade de negócio foi oficialmente removida.

A interface Desktop deixou de ser a interface principal e sua remoção completa dependerá da verificação de dependências compartilhadas.

Caso uma funcionalidade seja oficialmente removida, este documento deverá registrar:

- motivo

- versão

- alternativa adotada

---

# 13. Princípios Funcionais

Todas as funcionalidades do Financeiro Pro devem respeitar os seguintes princípios.

✅ Resolver problemas reais.

✅ Interface simples.

✅ Poucos cliques.

✅ Reutilizar regras existentes.

✅ Não duplicar funcionalidades.

✅ Manter consistência dos dados.

---

# 14. Fluxo Funcional do Sistema

```

Usuário / Fonte Externa

↓

Interpretação ou Cadastro

↓

Validação

↓

Transaction Service

↓

Persistência

↓

Atualização

↓

Visualização

↓

Análise

```

Todo novo módulo deverá integrar-se a esse fluxo sem criar comportamentos paralelos.

---

# 15. Considerações Finais

As funcionalidades do Financeiro Pro evoluem continuamente.

Entretanto, a filosofia do produto permanece constante:

Adicionar funcionalidades apenas quando elas aumentarem o valor entregue ao usuário.

O objetivo do sistema não é possuir o maior número de recursos.

O objetivo é oferecer uma experiência simples, confiável e eficiente para controle financeiro pessoal.

Toda nova funcionalidade deverá preservar esse compromisso.
