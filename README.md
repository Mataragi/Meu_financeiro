# 💰 Financeiro Pro

> **Controle financeiro pessoal com foco em simplicidade, confiabilidade e evolução sustentável.**

O **Financeiro Pro** é uma aplicação de controle financeiro pessoal criada para substituir uma planilha por uma ferramenta própria, simples de usar no dia a dia e construída com princípios reais de engenharia de software.

O projeto começou como uma solução para uma necessidade pessoal e evoluiu para um laboratório prático de **programação, arquitetura, modelagem de dados, refatoração, documentação, controle de versão e evolução incremental de produto**.

---

## 🎯 Visão do produto

O Financeiro Pro não tem como objetivo se tornar um sistema financeiro excessivamente complexo.

A proposta é deliberadamente simples:

> **Resolver poucos problemas importantes extremamente bem.**

O produto prioriza:

- simplicidade de uso;
- confiabilidade dos dados;
- poucos cliques;
- regras financeiras consistentes;
- baixo acoplamento;
- manutenibilidade;
- evolução incremental;
- documentação técnica;
- qualidade antes de quantidade.

A intenção é construir um sistema útil hoje e suficientemente sólido para evoluir amanhã.

---

## ✨ Funcionalidades

### 💳 Transações

- Cadastro de entradas e saídas;
- edição de lançamentos;
- exclusão individual e em lote;
- filtros por período e status;
- busca por descrição;
- controle de status;
- categorias;
- vencimentos;
- métricas financeiras.

### 📦 Parcelamentos

- criação automática de parcelas;
- cálculo de competência por mês e ano;
- identificação por grupo de parcelamento;
- status individual por parcela;
- baixa individual ou em lote;
- exclusão de grupos de parcelamento.

### 🤝 Dívidas informais

Controle separado para valores emprestados entre pessoas, mantendo esse domínio independente do fluxo principal de transações.

### 📥 Importação de extratos

- Importação de arquivos CSV;
- processamento de extratos bancários;
- conversão dos registros para o modelo de transações;
- preparação para uma futura evolução do importador com validação, prévia e seleção de registros.

### 💾 Backup

- Exportação de dados;
- geração de backup em CSV;
- restauração de dados.

### 📱 Interface

A aplicação possui atualmente uma experiência **mobile-first**, com componentes organizados para os principais fluxos de interação.

A interface continua em processo de evolução para uma experiência cada vez mais simples, responsiva e consistente.

---

# 🏗️ Arquitetura

O Financeiro Pro utiliza uma aplicação monolítica organizada em camadas, com responsabilidades progressivamente separadas.

```text
┌──────────────────────────────┐
│            Usuário           │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       Interface / UI         │
│          Streamlit           │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          Components          │
│   apresentação e interação   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│           Services           │
│     regras e casos de uso    │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          Repository          │
│      acesso à persistência   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│     Supabase / PostgreSQL    │
└──────────────────────────────┘
