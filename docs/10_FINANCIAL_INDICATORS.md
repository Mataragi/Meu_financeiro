# Indicadores Financeiros Consolidados

## Contrato da primeira entrega

O aplicativo calcula três indicadores independentes para uma data de
referência, normalmente o último dia do mês selecionado:

- **Saldo Disponível**: saldo inicial configurado, acrescido de receitas
  liquidadas e reduzido por despesas liquidadas desde a data-base.
- **Resultado Acumulado**: receitas menos despesas pela competência original,
  independentemente da data de liquidação.
- **Saldo Projetado**: saldo disponível mais receitas pendentes menos despesas
  pendentes com competência até a referência.

`data_base` representa o início do dia; liquidações ocorridas nela entram no
cálculo normalmente. O saldo inicial é configuração consolidada de
disponibilidades controladas, não uma transação artificial.

## Cartões de crédito

Uma compra no cartão é uma despesa única pela competência da fatura. A baixa
da fatura registra `data_liquidacao` nos lançamentos de compra quitados e não
cria outra despesa. Assim, o resultado reconhece a compra na competência e o
saldo disponível reconhece sua saída quando o pagamento ocorre.

## Pagamentos parciais

O modelo atual possui um valor, um status e uma única `data_liquidacao` por
transação. Portanto, ele **não suporta pagamento parcial com segurança**:
um pagamento parcial exige pelo menos dois valores liquidados em datas que
podem ser diferentes, além de um saldo remanescente.

Nesta entrega, a baixa será integral; a interface futura não deverá oferecer
pagamento parcial. A evolução correta é uma tabela filha de liquidações, com
`transacao_id`, `valor` e `data_liquidacao`, da qual se calcula o valor
liquidado, o saldo pendente e o status. Não será criada nesta etapa para evitar
simular ou duplicar despesas de cartão.

## Compatibilidade histórica

Registros antigos pagos sem `data_liquidacao` usam o mês/ano de competência
apenas como aproximação de caixa. Registros pendentes permanecem pendentes.
Nenhum dado histórico é atualizado automaticamente.

### Restauração e importação histórica

`restaurar_backup_historico()` é a única porta de restauração de backups. Ela
valida todo o lote antes de emitir um único insert em lote; por isso um
registro inválido não produz restauração parcial. Nesse fluxo controlado, um
registro `Pago` sem `data_liquidacao` é preservado como legado, inclusive
quando o CSV representa a ausência como uma célula vazia. A criação comum
continua usando `inserir_dados()` e exige data efetiva para todo novo `Pago`.

Na importação de extrato, a data existente no campo `Data` da origem é usada
como `data_transacao` e `data_liquidacao`. Linhas sem data válida são
descartadas; o sistema não fabrica datas de pagamento. O backup é gerado por
paginação do histórico, para não depender do limite de uma única resposta da
Data API.

Edições e exclusões retroativas recalculam os indicadores históricos. O
produto não mantém, nesta entrega, um log imutável do estado conhecido em cada
instante.

## Acesso à configuração consolidada

O aplicativo atual não usa Supabase Auth nem separa dados por usuário. A
configuração de disponibilidade fica protegida por RLS sem policies públicas:
somente o `service_role` do backend Streamlit recebe privilégios de leitura e
escrita. A chave deve existir exclusivamente como
`SUPABASE_SERVICE_ROLE_KEY` nos secrets do servidor; chaves `anon` não são
aceitas pelo cliente da aplicação. Essa estratégia não deve ser reutilizada em
um futuro produto multiusuário, que precisará de identidade e policies por
proprietário.

## Histórico completo e consistência

O serviço financeiro lê o histórico em páginas por chave, ordenadas por `id`.
Não depende de uma única resposta do Data API, que pode ser limitada pelo
Supabase.

Uma transação pendente não pode ter `data_liquidacao`. Registros pagos sem a
data continuam permitidos apenas para compatibilidade histórica e usam a
competência como aproximação de caixa. Registros com status ou data inválidos
são rejeitados antes do cálculo. O serviço expõe a quantidade de pagamentos
legados sem data para que essa aproximação nunca seja silenciosa; a baixa nova
da Etapa 2 exige a data efetiva de liquidação.

## Etapa 2: persistência e liquidação

`services.disponibilidade_service` persiste exclusivamente a configuração
consolidada `id=1`. `carregar_saldo_inicial()` retorna `None` quando não existe
configuração e retorna um saldo válido quando o valor é `0,00`; portanto a
ausência nunca é confundida com saldo zero. `salvar_saldo_inicial()` normaliza
valor e data-base e faz `upsert` pela chave fixa, sem criar transação.

`services.transaction_service.liquidar_transacoes(ids, data)` é a porta
central para baixar transações. Ela exige uma data ISO válida, carrega e valida
todos os ids, preserva `mes` e `ano`, e atualiza apenas pendências sem
`data_liquidacao`. O `UPDATE` também contém essas pré-condições, evitando que
uma segunda baixa concorrente seja aceita. Após sucesso, os caches de consulta
mensal e de histórico completo são invalidados.

`dar_baixa_registro`, `dar_baixa_multiplos` e
`atualizar_status_multiplos(..., "Pago", data)` delegam para essa mesma regra.
Inserções novas — inclusive importações externas e parcelamentos — exigem
`data_liquidacao` quando o status for `Pago`. A leitura e o cálculo dos dados
legados não são alterados.

Para cartões, `liquidar_fatura_cartao(ids, data)` somente aceita lançamentos
de Crédito, que sejam despesas pendentes, sem data de liquidação e da mesma
competência. Ele os liquida em lote: não insere um lançamento de fatura, nem muda a
competência das compras. O modelo ainda não possui uma entidade de fatura ou
de parcelas liquidadas; por isso a seleção dos ids correspondentes à fatura e
a experiência de captura da data dependem da etapa de interface. Pagamentos
parciais continuam deliberadamente indisponíveis.

## Verificação

Os testes da Etapa 2 usam repositórios simulados para cobrir configuração
ausente/zero, criação e atualização idempotentes, baixa individual e em lote,
data inválida, duplicidade, preservação de competência, fatura de cartão,
parcelamentos, importação externa, invalidação de cache e leitura de legado.
Nenhum deles acessa ou altera o banco de produção.

## Atomicidade da liquidação

A persistência da baixa usa a RPC public.liquidar_transacoes(bigint[], date, jsonb), criada pela migração 20261114182518_atomic_batch_liquidation.sql. A chamada ocorre em uma única transação PostgreSQL: os registros são bloqueados com FOR UPDATE em ordem crescente de ID, todos são validados e somente então o lote é atualizado. Uma falha em qualquer linha aborta a instrução e reverte o lote inteiro. O mesmo contrato atende à baixa individual, à baixa em lote e à liquidação das compras de cartão selecionadas.

A função usa SECURITY INVOKER, search_path vazio e nomes de objetos qualificados. A execução é revogada de PUBLIC, anon e authenticated, sendo concedida somente a service_role. Essa função não concede privilégios adicionais sobre a tabela; o backend continua responsável por usar a chave secreta no servidor.

Durante a liquidação, somente estes campos descritivos podem ser atualizados junto com status e data efetiva: descricao, categoria, forma_pagamento, vencimento e data_transacao. Valor, competência, identificador, status, data de liquidação e qualquer campo não listado são rejeitados. Isso evita que uma ação de pagamento altere o valor ou a competência da obrigação.

### Verificação PostgreSQL isolada

Os testes de integração criam um PostgreSQL 16 efêmero em Docker, com rede desabilitada, e removem o container ao final. Eles exercitam liquidação individual/lote, validação de IDs e estados, rollback provocado por trigger, concorrência entre duas chamadas e privilégios da RPC. Para executá-los, use:

FINANCEIRO_PRO_TEST_POSTGRES=1 ./.venv/bin/pytest -q tests/test_liquidacao_postgres_integration.py

A suíte normal mantém esses testes opcionais (skip) quando a variável de ambiente não está habilitada. Nenhum teste utiliza a URL, as chaves ou os dados do Supabase de produção.

## Integração da interface de liquidação

A interface Mobile captura a data efetiva antes de solicitar uma baixa. As baixas individuais pelo editor também solicitam essa data ao mudar uma transação pendente para paga. Para evitar misturar alteração de valor e liquidação em uma mesma operação, o editor exige salvar a mudança de valor separadamente antes da baixa.

Compras de despesa com forma de pagamento Crédito são separadas da baixa genérica. A ação Pagar fatura apresenta quantidade e total das compras pendentes da competência atualmente selecionada e chama o serviço centralizado de liquidação de fatura; não cria um lançamento adicional. Na interface Mobile, é obrigatório selecionar um mês específico para pagar a fatura, evitando agrupar competências diferentes.

A data inicial sugerida pela interface é a data local atual, mas pode ser alterada antes da confirmação. O serviço continua sendo a autoridade de validação e preservação da competência.

A interface depende da migração RPC 20261114182518_atomic_batch_liquidation.sql estar aplicada no ambiente Supabase. No ambiente de produção atualmente conectado, essa migração já foi aplicada e verificada.

## Indicadores na interface Mobile

A lista de transações oferece filtros independentes de tipo (Todos,
Receitas ou Despesas), status, categoria e forma de pagamento. O filtro de
tipo normaliza os rótulos históricos Entrada/Saída para Receita/Despesa.
Esses filtros afetam somente a lista e seus detalhes, nunca os indicadores.

A interface única Mobile apresenta dois grupos de três cartões, ambos
independentes dos filtros da lista de transações:

**Resumo do mês**, calculado somente sobre a competência selecionada:

- Pago: total de despesas pagas na competência.
- Pendente: total de despesas pendentes na competência.
- Saldo calculado: receitas pagas menos despesas pagas na competência.

**Posição financeira**, calculada pelo histórico completo:

- Saldo disponível: saldo inicial mais receitas e despesas efetivamente
  liquidadas desde a data-base.
- Resultado acumulado: receitas menos despesas por competência até a
  referência selecionada.
- Saldo projetado: saldo disponível acrescido das receitas pendentes e
  reduzido pelas despesas pendentes até a referência.

Os grupos não se substituem. O resumo mensal preserva a leitura operacional
utilizada anteriormente; a posição financeira acrescenta a visão consolidada
de caixa, resultado e projeção.

A configuração do saldo inicial é feita na própria interface Mobile, no
expander **Configurar saldo inicial**. O usuário informa o valor real e a
data-base. A data-base representa o início do dia; o saldo informado deve ser
o valor disponível antes das movimentações daquele dia. A ausência de
configuração nunca é convertida automaticamente em saldo zero.

Quando a configuração já existe, a interface permite ajustá-la, avisando que
a alteração recalcula os indicadores sem modificar os lançamentos. A
referência anterior à data-base não é calculada.

A interface Mobile captura a data efetiva antes de solicitar uma baixa. As
baixas individuais pelo editor também solicitam essa data ao mudar uma
transação pendente para paga. Para evitar misturar alteração de valor e
liquidação em uma mesma operação, o editor exige salvar a mudança de valor
separadamente antes da baixa.

Compras de despesa com forma de pagamento Crédito são separadas da baixa
genérica. A ação Pagar fatura apresenta quantidade e total das compras
pendentes da competência atualmente selecionada e chama o serviço
centralizado de liquidação de fatura; não cria um lançamento adicional. Na
interface Mobile, é obrigatório selecionar um mês específico para pagar a
fatura, evitando agrupar competências diferentes.

As ações de liquidação apresentam sucesso somente após a confirmação do
serviço. Falhas esperadas de validação, concorrência ou comunicação da RPC
recebem mensagem segura e registram o tipo técnico da falha no log; exceções
inesperadas continuam visíveis para diagnóstico.
