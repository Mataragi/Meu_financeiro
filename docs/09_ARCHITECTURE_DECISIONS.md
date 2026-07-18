# Financeiro Pro

# Architecture Decisions

**Versão do Documento:** 1.0

**Compatível com:** Financeiro Pro v0.9.x

**Status:** Documento Vivo

**Última atualização:** Julho de 2026

---

# 1. Objetivo

Este documento registra as principais decisões arquiteturais adotadas durante o desenvolvimento do Financeiro Pro.

Cada decisão possui uma justificativa técnica e representa um compromisso arquitetural do projeto.

O objetivo é preservar o contexto das escolhas realizadas e orientar futuras evoluções do sistema.

---

# 2. Como utilizar este documento

Cada decisão arquitetural deve conter:

- Contexto
- Problema
- Decisão
- Justificativa
- Consequências

Novas decisões deverão ser adicionadas ao final deste documento utilizando uma numeração sequencial.

---

# ADR-001

## Utilização do Supabase

### Contexto

O projeto inicialmente utilizava armazenamento local.

### Problema

Os dados não possuíam persistência adequada e dificultavam futuras evoluções.

### Decisão

Adotar o Supabase como banco oficial da aplicação.

### Justificativa

- Banco relacional.
- API pronta.
- Escalabilidade.
- Integração simples com Python.

### Consequências

Toda persistência passa a depender do Supabase.

---

# ADR-002

## Transações como única fonte do fluxo financeiro

### Contexto

Diversos módulos dependem das movimentações financeiras.

### Problema

Duplicação de dados poderia gerar inconsistências.

### Decisão

Toda movimentação financeira será registrada exclusivamente na tabela `transacoes`.

### Justificativa

Centralização dos dados.

Maior consistência.

Menor complexidade.

### Consequências

Novos módulos deverão consumir informações da tabela `transacoes`.

---

# ADR-003

## Separação entre Fluxo Financeiro e Patrimônio

### Contexto

Investimentos estavam sendo registrados como despesas.

### Problema

Essa abordagem distorcia indicadores financeiros.

### Decisão

Criar futuramente um domínio específico para patrimônio.

### Justificativa

Fluxo financeiro e patrimônio representam conceitos distintos.

### Consequências

O módulo Patrimônio utilizará estrutura própria.

---

# ADR-004

## Parcelamentos como transações independentes

### Contexto

Era necessário controlar cada parcela individualmente.

### Problema

Modelos baseados em uma única compra dificultavam filtros e baixas.

### Decisão

Cada parcela será registrada como uma transação independente.

### Justificativa

Maior flexibilidade.

Consultas simplificadas.

Baixa individual.

### Consequências

Todas as parcelas compartilham um identificador de grupo.

---

# ADR-005

## Arquitetura Modular

### Contexto

O crescimento do projeto aumentou a complexidade do código.

### Problema

Grande concentração de responsabilidades em poucos arquivos.

### Decisão

Separar o projeto em módulos.

### Estrutura

- components
- services
- utils

### Consequências

Maior organização.

Maior facilidade para manutenção.

---

# ADR-006

## Mobile First

### Contexto

O principal uso do sistema ocorre em dispositivos móveis.

### Problema

Desktop e Mobile evoluíam de forma independente.

### Decisão

Adotar Mobile como referência principal para evolução do produto.

### Justificativa

Melhor experiência para o usuário.

### Consequências

A tendência é evoluir para uma interface responsiva única.

---

# ADR-007

## Separação entre Interface e Regras de Negócio

### Contexto

Misturar interface e lógica dificulta manutenção.

### Decisão

A interface apenas apresenta informações.

Toda regra de negócio deverá permanecer fora dos componentes visuais.

### Consequências

Maior reutilização do código.

---

# ADR-008

## Documentação como parte da arquitetura

### Contexto

O crescimento do projeto tornou difícil lembrar todas as decisões tomadas.

### Problema

Conhecimento concentrado apenas no histórico de conversas.

### Decisão

Toda alteração arquitetural relevante deverá ser documentada.

### Consequências

Maior previsibilidade.

Facilidade para manutenção.

Maior qualidade do projeto.

---

# ADR-009

## Evolução incremental

### Contexto

Projetos que crescem rapidamente tendem a acumular dívida técnica.

### Decisão

O Financeiro Pro evoluirá por etapas.

Cada funcionalidade deverá consolidar a base existente antes da próxima evolução.

### Consequências

Menor retrabalho.

Maior estabilidade.

Arquitetura mais consistente.

---

# 3. Processo para Novas ADRs

Uma nova ADR deverá ser criada sempre que ocorrer:

- mudança estrutural;
- alteração de domínio;
- troca de tecnologia;
- mudança de banco de dados;
- alteração na arquitetura;
- mudança de estratégia de desenvolvimento.

---

# 4. Princípios Arquiteturais

Todas as decisões deverão preservar os seguintes princípios:

- Simplicidade.
- Baixo acoplamento.
- Alta coesão.
- Evolução incremental.
- Reutilização.
- Clareza.
- Escalabilidade.
- Manutenibilidade.

---

# 5. Considerações Finais

As Architecture Decision Records representam a memória técnica do Financeiro Pro.

Elas registram não apenas as decisões tomadas, mas também o contexto que motivou cada escolha.

A arquitetura do projeto poderá evoluir ao longo do tempo.

Entretanto, toda evolução deverá preservar a consistência, a simplicidade e a qualidade técnica do sistema.