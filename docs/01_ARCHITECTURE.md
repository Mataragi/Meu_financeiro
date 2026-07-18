# Financeiro Pro

# Software Architecture

**Versão:** 1.0
**Status:** Documento Vivo
**Última atualização:** Julho de 2026

---

# 1. Visão Geral da Arquitetura

O Financeiro Pro é uma aplicação desenvolvida utilizando arquitetura em camadas.

Seu principal objetivo é separar interface, regras de negócio, acesso aos dados e utilidades, facilitando manutenção, evolução e futuras migrações tecnológicas.

A aplicação atualmente utiliza Streamlit como camada de apresentação e Supabase como banco de dados.

Embora seja um sistema monolítico, sua estrutura foi organizada para reduzir acoplamento entre os módulos.

---

# 2. Arquitetura Geral

```
                 Usuário
                     │
                     ▼
            Interface Streamlit
                     │
                     ▼
              Componentes (UI)
                     │
                     ▼
          Camada de Serviços (Business)
                     │
                     ▼
          Cliente Supabase (Data Access)
                     │
                     ▼
              Banco de Dados
```

Cada camada possui responsabilidades específicas.

Nenhuma camada deve assumir responsabilidades pertencentes à outra.

---

# 3. Estrutura do Projeto

```
Financeiro Pro

├── app.py
│
├── components/
│
├── services/
│
├── utils/
│
├── docs/
│
├── .streamlit/
│
└── requirements.txt
```

---

# 4. Responsabilidade de Cada Pasta

## app.py

Responsável apenas por iniciar a aplicação.

Suas responsabilidades são:

- configurar Streamlit;
- carregar interface;
- controlar modo de execução;
- iniciar componentes principais.

Ele nunca deve conter regras de negócio.

---

## components/

Contém exclusivamente elementos da interface.

Exemplos:

- telas
- formulários
- tabelas
- botões
- métricas
- filtros

Componentes podem solicitar dados aos Services.

Nunca devem acessar diretamente o banco de dados.

---

## services/

Representa a camada de negócio.

É responsável por:

- consultas
- inserções
- atualizações
- exclusões
- parcelamentos
- regras financeiras
- integração com Supabase

Toda regra importante deve nascer aqui.

---

## utils/

Contém funções auxiliares.

Exemplos:

- formatação
- processamento
- conversões
- leitura de arquivos

Nunca devem depender da interface.

---

## docs/

Contém toda documentação oficial do projeto.

É considerada parte integrante da aplicação.

Mudanças arquiteturais importantes obrigatoriamente exigem atualização desta pasta.

---

# 5. Fluxo Principal da Aplicação

Quando um usuário realiza uma ação, o fluxo esperado é:

```
Usuário

↓

Interface

↓

Components

↓

Services

↓

Supabase

↓

Banco

↓

Services

↓

Components

↓

Interface
```

A interface nunca deve conhecer detalhes do banco.

Toda comunicação ocorre através dos serviços.

---

# 6. Fluxo de Cadastro

```
Usuário

↓

Formulário

↓

Validação

↓

Service

↓

Supabase

↓

Tabela transacoes

↓

Limpeza do cache

↓

Atualização da Interface
```

---

# 7. Fluxo de Consulta

```
Usuário

↓

Filtro

↓

Services

↓

Supabase

↓

DataFrame

↓

Processamento

↓

Tabela

↓

Usuário
```

---

# 8. Camadas da Aplicação

## Interface

Responsável apenas pela experiência do usuário.

Não deve conter:

- SQL
- consultas
- regras financeiras
- lógica de parcelamentos

---

## Serviços

Responsáveis por toda regra de negócio.

Exemplos:

- parcelamento
- atualização
- filtros
- clonagem
- backup

---

## Persistência

Responsável por comunicação com Supabase.

Seu único objetivo é transportar dados.

---

# 9. Banco de Dados

Atualmente o sistema possui duas entidades principais.

```
transacoes

↓

Fluxo financeiro
```

```
dividas_informais

↓

Controle de dívidas pessoais
```

No futuro poderão existir novas entidades sem alterar o conceito principal da arquitetura.

---

# 10. Fonte Oficial dos Dados

Uma decisão arquitetural importante:

A tabela **transacoes** é a principal fonte de verdade do sistema.

Ela alimenta:

- Dashboard
- Timeline
- Relatórios
- Filtros
- Métricas
- Parcelamentos

Novas funcionalidades devem reutilizar essa tabela sempre que possível.

---

# 11. Cache

O sistema utiliza dois níveis de cache.

## cache_resource

Responsável por manter o cliente Supabase.

## cache_data

Responsável pelas consultas.

Sempre que ocorrer uma alteração no banco, o cache deverá ser invalidado.

---

# 12. Princípios Arquiteturais

O projeto segue os seguintes princípios.

## Responsabilidade Única

Cada módulo deve possuir apenas uma responsabilidade principal.

---

## Baixo Acoplamento

Módulos devem conhecer o mínimo possível uns dos outros.

---

## Alta Coesão

Cada arquivo deve tratar apenas de assuntos relacionados ao seu domínio.

---

## Reutilização

Antes de criar uma função nova deve ser avaliado se já existe uma implementação semelhante.

Duplicação é considerada dívida técnica.

---

## Escalabilidade

Toda implementação deve considerar futuras expansões.

Entre elas:

- Login
- Multiusuário
- Flutter
- APIs
- Relatórios

---

# 13. Arquitetura Atual

Atualmente a arquitetura encontra-se em transição.

Pontos positivos:

✔ Separação entre Components, Services e Utils.

✔ Uso de cache.

✔ Organização do projeto.

✔ Modularização da interface mobile.

Pontos em evolução:

- database.py concentra muitas responsabilidades.

- Dashboard ainda realiza algumas operações diretamente.

- Existem regras duplicadas entre interfaces.

Esses pontos serão tratados gradualmente.

---

# 14. Arquitetura Alvo

A arquitetura desejada é:

```
Interface

↓

Components

↓

Application Services

↓

Domain Services

↓

Repository

↓

Supabase
```

Essa separação permitirá:

- maior reutilização;
- testes automatizados;
- migração para Flutter;
- criação de API;
- crescimento do sistema.

---

# 15. Regras Arquiteturais

Toda nova implementação deverá obedecer às seguintes regras.

✅ Componentes não acessam banco.

✅ Toda regra financeira pertence aos Services.

✅ Utilitários permanecem independentes.

✅ Código duplicado deve ser evitado.

✅ Documentação deve acompanhar mudanças importantes.

---

# 16. Evolução da Arquitetura

A arquitetura evoluirá na seguinte ordem.

Fase 1

- Consolidação dos Services

Fase 2

- Timeline

Fase 3

- Recorrências

Fase 4

- Organização Patrimonial

Fase 5

- Login

Fase 6

- Multiusuário

Fase 7

- Flutter

Cada etapa deverá preservar os princípios definidos neste documento.

---

# 17. Considerações Finais

A arquitetura do Financeiro Pro foi projetada para crescer de forma incremental.

O objetivo não é construir um sistema complexo.

O objetivo é construir um sistema simples, organizado e preparado para evoluir.

Toda decisão técnica deverá priorizar:

1. Clareza.

2. Organização.

3. Simplicidade.

4. Reutilização.

5. Escalabilidade.

A arquitetura deve servir ao produto.

Nunca o contrário.