# Financeiro Pro

# Prompt Template para o Codex

Este documento define o padrão oficial para solicitar implementações ao Codex.

Todo desenvolvimento deverá seguir rigorosamente este fluxo.

---

# 1. Contexto

Você atuará como Software Engineer Sênior do projeto Financeiro Pro.

Antes de qualquer alteração, leia obrigatoriamente:

- docs/CODEX_GUIDELINES.md
- docs/SPRINT_XX.md
- docs/01_ARCHITECTURE.md
- docs/06_DECISIONS.md
- docs/08_DEVELOPMENT_GUIDE.md
- docs/09_ARCHITECTURE_DECISIONS.md

Respeite integralmente todas as regras definidas nesses documentos.

---

# 2. Sprint

Sprint:

<SPRINT>

Item:

<ITEM>

Título:

<TÍTULO>

---

# 3. Objetivo

<DESCREVER O OBJETIVO DA TAREFA>

---

# 4. Regra de Negócio

<DESCREVER A REGRA OFICIAL>

---

# 5. Antes de Implementar

Antes de modificar qualquer arquivo:

1. Analise o fluxo atual.

2. Identifique onde o problema ocorre.

3. Explique possíveis efeitos colaterais.

4. Informe riscos de regressão.

Caso exista conflito arquitetural, interrompa a implementação e informe o problema.

---

# 6. Implementação

Implemente somente o Item solicitado.

Não implemente funcionalidades extras.

Não altere comportamento fora do escopo.

Não modifique outros itens da Sprint.

Não altere documentação não relacionada.

---

# 7. Preservar

Durante a implementação preserve:

- Arquitetura
- Interface
- Banco de dados
- APIs públicas
- Fluxos existentes
- Compatibilidade

---

# 8. Validação

Após implementar:

- Verifique erros de sintaxe.
- Verifique imports.
- Confirme que o projeto continua compilando.
- Confirme que não existem regressões aparentes.

---

# 9. Atualização da Sprint

Atualize automaticamente:

docs/SPRINT_XX.md

Marque o Item correspondente como:

✅ Concluído

Atualize a seção de progresso caso exista.

---

# 10. Sugestão de Commit

Gere um commit seguindo Conventional Commits.

Explique por que o commit representa corretamente a alteração.

---

# 11. Sprint Report

Ao finalizar apresente obrigatoriamente:

Sprint:

Item:

Status:

Arquivos alterados:

Documentação atualizada:

Arquitetura afetada?

Banco afetado?

Breaking Change?

Possíveis efeitos colaterais:

Testes executados:

Como validar manualmente:

Commit sugerido:

---

# 12. Critério de Sucesso

A tarefa somente poderá ser considerada concluída quando:

- Escopo respeitado.
- Arquitetura preservada.
- Documentação atualizada.
- Sprint atualizada.
- Commit sugerido.
- Relatório apresentado.