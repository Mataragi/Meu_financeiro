-- Metadados da operação financeira.
-- Migration restaurada no repositório a partir do estado aplicado no Supabase.
-- Não altera nem preenche registros históricos.

alter table public.transacoes
    add column if not exists forma_pagamento text null;

alter table public.transacoes
    add column if not exists data_transacao date null;
