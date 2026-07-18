# Financeiro Pro

# Decisions Log

**Versão do Documento:** 1.0

**Compatível com:** Financeiro Pro v0.9.x

**Status:** Documento Vivo

**Última atualização:** Julho de 2026

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

# 4. Decisões de Arquitetura

---

## DEC-003

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

## DEC-004

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

## DEC-005

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

## DEC-006

### Interface Mobile será a principal interface do projeto.

### Problema

A interface Desktop e Mobile evoluíam separadamente.

### Decisão

A evolução do sistema será baseada na experiência Mobile.

### Justificativa

O principal uso do Financeiro Pro ocorre em dispositivos móveis.

### Impacto

A tendência é evoluir para uma interface única responsiva.

---

# 5. Decisões Técnicas

---

## DEC-007

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

## DEC-008

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

## DEC-009

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

# 6. Decisões Futuras

Algumas decisões ainda dependem da evolução do projeto.

Entre elas:

- Flutter
- Multiusuário
- API pública
- Open Finance
- Inteligência Artificial

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