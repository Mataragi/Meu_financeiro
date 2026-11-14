-- Fundação aditiva para os três indicadores financeiros.
-- Esta migração não altera nem recalcula registros históricos.

alter table public.transacoes
    add column if not exists data_liquidacao date null;

-- Mantém os registros pagos legados sem data de liquidação, mas impede que
-- novos dados afirmem simultaneamente que a transação está pendente e foi
-- liquidada. A data possui tipo date, portanto datas inválidas são recusadas
-- pelo PostgreSQL.
alter table public.transacoes
    add constraint transacoes_liquidacao_status_check
    check (data_liquidacao is null or status = 'Pago');

create index if not exists transacoes_data_liquidacao_idx
    on public.transacoes (data_liquidacao);

create index if not exists transacoes_competencia_idx
    on public.transacoes (ano, mes);

-- A aplicação começa com uma única disponibilidade consolidada. O saldo é um
-- dado de configuração, não uma transação artificial de receita ou despesa.
create table if not exists public.configuracao_disponibilidade (
    id smallint primary key default 1,
    saldo_inicial numeric(14, 2) not null,
    data_base date not null,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now(),
    constraint configuracao_disponibilidade_unica check (id = 1)
);

alter table public.configuracao_disponibilidade enable row level security;

-- O produto atual não usa Supabase Auth nem tem uma coluna de propriedade por
-- usuário. A única aplicação autorizada é o backend Streamlit, que deve usar
-- uma service-role key mantida exclusivamente nos secrets do servidor.
-- Não conceder acesso ao Data API para anon/authenticated evita expor a
-- configuração consolidada sem um predicado de autorização verificável.
revoke all on table public.configuracao_disponibilidade from anon, authenticated;
grant select, insert, update on table public.configuracao_disponibilidade
    to service_role;
