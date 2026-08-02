# CODEX GUIDELINES

Este documento define as regras oficiais para qualquer implementação realizada pelo Codex no projeto Financeiro Pro.

Todas as tarefas deverão respeitar integralmente estas diretrizes.

---

# Princípios Gerais

Sempre:

- Respeitar a arquitetura oficial do projeto.
- Respeitar a documentação vigente.
- Não alterar mais de um item da Sprint por execução.
- Nunca modificar documentação não relacionada.
- Nunca implementar funcionalidades fora do escopo solicitado.
- Gerar commits seguindo o padrão Conventional Commits.
- Entregar checklist e relatório final da Sprint.
- Sempre analisar possíveis efeitos colaterais antes de alterar o código.
- Nunca alterar mais arquivos do que o necessário para concluir a tarefa.
- Preservar comportamento existente, salvo quando a Sprint definir o contrário.

---

# Alterações Estruturais

Nenhuma tarefa que envolva mais de um domínio da arquitetura poderá ser implementada em uma única execução.

Exemplos de domínios:

- Persistência
- Cache
- Interface
- Regras de negócio
- Banco de dados
- Arquitetura

Toda alteração estrutural deverá ser dividida em subtarefas menores.

Cada subtarefa deverá possuir:

- escopo próprio;
- validação independente;
- commit próprio;
- possibilidade de rollback.

Evite grandes refatorações em uma única execução.

---

# Antes de Implementar

Antes de escrever qualquer código o Codex deverá:

1. Analisar a arquitetura atual.
2. Identificar possíveis conflitos.
3. Explicar riscos de regressão.
4. Informar efeitos colaterais esperados.
5. Confirmar que a tarefa pertence ao Item atual da Sprint.

Caso exista conflito arquitetural, interromper a implementação e solicitar decisão antes de prosseguir.

---

# Durante a Implementação

Toda alteração deverá:

- preservar compatibilidade;
- evitar duplicação de código;
- manter baixo acoplamento;
- manter alta coesão;
- preservar APIs públicas;
- minimizar impacto sobre outros módulos.

---

# Após Implementar

Ao concluir uma tarefa o Codex deverá obrigatoriamente:

- Atualizar a Sprint correspondente.
- Atualizar documentação quando solicitado.
- Gerar sugestão de commit.
- Apresentar Sprint Report.
- Informar arquivos alterados.
- Informar possíveis riscos.
- Informar como validar manualmente.

---

# Limites

O Codex NÃO deverá:

- implementar funcionalidades fora da Sprint;
- alterar regras de negócio sem aprovação;
- criar novas arquiteturas sem justificativa;
- modificar documentos não relacionados;
- executar grandes refatorações sem subdivisão;
- remover código sem explicar o motivo.

---

# Objetivo

O papel do Codex é executar tarefas previamente planejadas.

O planejamento, arquitetura, validação técnica e decisões de produto permanecem sob responsabilidade do processo de desenvolvimento do Financeiro Pro.