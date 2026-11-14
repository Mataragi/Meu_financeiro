-- Liquidação integral e concorrente-segura de uma ou várias transações.
-- A chamada RPC executa como uma única instrução/transação PostgreSQL.

create or replace function public.liquidar_transacoes(
    p_ids bigint[],
    p_data_liquidacao date,
    p_atualizacoes jsonb default '{}'::jsonb
)
returns setof public.transacoes
language plpgsql
security invoker
set search_path = ''
as $function$
declare
    v_quantidade_esperada bigint;
    v_quantidade_unica bigint;
    v_quantidade_encontrada bigint;
    v_quantidade_invalidas bigint;
    v_quantidade_atualizada bigint;
    v_campos_nao_permitidos text[];
    v_atualizacoes public.transacoes%rowtype;
begin
    if p_ids is null or pg_catalog.cardinality(p_ids) = 0 then
        raise exception 'Informe ao menos uma transação para liquidação.'
            using errcode = '22023';
    end if;

    if pg_catalog.array_position(p_ids, null::bigint) is not null then
        raise exception 'A lista de liquidação contém identificador nulo.'
            using errcode = '22023';
    end if;

    if p_data_liquidacao is null then
        raise exception 'A data efetiva de liquidação é obrigatória.'
            using errcode = '22023';
    end if;

    if p_atualizacoes is null
       or pg_catalog.jsonb_typeof(p_atualizacoes) <> 'object' then
        raise exception 'As atualizações adicionais devem ser um objeto JSON.'
            using errcode = '22023';
    end if;

    select pg_catalog.count(*)
      into v_quantidade_esperada
      from pg_catalog.unnest(p_ids) as entrada(id);

    select pg_catalog.count(distinct entrada.id)
      into v_quantidade_unica
      from pg_catalog.unnest(p_ids) as entrada(id);

    if v_quantidade_unica <> v_quantidade_esperada then
        raise exception 'A lista de liquidação contém identificadores duplicados.'
            using errcode = '22023';
    end if;

    select pg_catalog.array_agg(chave)
      into v_campos_nao_permitidos
      from pg_catalog.jsonb_object_keys(p_atualizacoes) as campos(chave)
     where chave not in (
        'descricao',
        'categoria',
        'forma_pagamento',
        'vencimento',
        'data_transacao'
     );

    if v_campos_nao_permitidos is not null then
        raise exception 'A liquidação contém campos não permitidos: %',
            pg_catalog.array_to_string(v_campos_nao_permitidos, ', ')
            using errcode = '22023';
    end if;

    -- Converte valores usando os tipos reais das colunas da tabela. Isso
    -- rejeita payloads incompatíveis sem construir SQL dinâmico.
    v_atualizacoes := pg_catalog.jsonb_populate_record(
        null::public.transacoes,
        p_atualizacoes
    );

    v_quantidade_esperada := pg_catalog.cardinality(p_ids);

    -- A ordenação reduz a possibilidade de deadlock entre lotes sobrepostos.
    -- O bloqueio permanece até o término da transação RPC.
    perform transacao.id
      from public.transacoes as transacao
     where transacao.id = any (p_ids)
     order by transacao.id
     for update of transacao;

    select pg_catalog.count(*)
      into v_quantidade_encontrada
      from public.transacoes as transacao
     where transacao.id = any (p_ids);

    if v_quantidade_encontrada <> v_quantidade_esperada then
        raise exception 'Uma ou mais transações não foram encontradas.'
            using errcode = 'P0002';
    end if;

    select pg_catalog.count(*)
      into v_quantidade_invalidas
      from public.transacoes as transacao
     where transacao.id = any (p_ids)
       and (
            transacao.status is distinct from 'Pendente'
            or transacao.data_liquidacao is not null
            or transacao.valor is null
            or transacao.valor::text = 'NaN'
       );

    if v_quantidade_invalidas > 0 then
        raise exception
            'Todas as transações devem estar pendentes, sem data de liquidação e possuir valor.'
            using errcode = '23514';
    end if;

    return query
    update public.transacoes as transacao
       set status = 'Pago',
           data_liquidacao = p_data_liquidacao,
           descricao = case when p_atualizacoes ? 'descricao'
                            then v_atualizacoes.descricao
                            else transacao.descricao end,
           categoria = case when p_atualizacoes ? 'categoria'
                            then v_atualizacoes.categoria
                            else transacao.categoria end,
           forma_pagamento = case when p_atualizacoes ? 'forma_pagamento'
                                  then v_atualizacoes.forma_pagamento
                                  else transacao.forma_pagamento end,
           vencimento = case when p_atualizacoes ? 'vencimento'
                             then v_atualizacoes.vencimento
                             else transacao.vencimento end,
           data_transacao = case when p_atualizacoes ? 'data_transacao'
                                 then v_atualizacoes.data_transacao
                                 else transacao.data_transacao end
     where transacao.id = any (p_ids)
       and transacao.status = 'Pendente'
       and transacao.data_liquidacao is null
       and transacao.valor is not null
       and transacao.valor::text <> 'NaN'
    returning transacao.*;

    get diagnostics v_quantidade_atualizada = row_count;
    if v_quantidade_atualizada <> v_quantidade_esperada then
        raise exception
            'Liquidação incompleta: esperadas % transações, atualizadas %.',
            v_quantidade_esperada,
            v_quantidade_atualizada
            using errcode = '40001';
    end if;
end;
$function$;

-- Funções recebem EXECUTE de PUBLIC por padrão. Restringimos explicitamente
-- a chamada ao backend que utiliza a chave service_role.
revoke all on function public.liquidar_transacoes(bigint[], date, jsonb)
    from public, anon, authenticated;
grant execute on function public.liquidar_transacoes(bigint[], date, jsonb)
    to service_role;
