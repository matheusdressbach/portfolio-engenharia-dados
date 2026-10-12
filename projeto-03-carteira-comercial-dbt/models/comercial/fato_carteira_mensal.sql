with compras as (
    select id_cliente, competencia, count(*) as pedidos
    from {{ ref('fato_pedidos') }}
    where status = 'faturado'
    group by id_cliente, competencia
), primeira_compra as (
    select id_cliente, min(competencia) as primeira_competencia
    from compras group by id_cliente
), carteira as (
    select
        c.id_cliente, c.chave_cliente, c.id_vendedor, c.regiao, c.ativo,
        m.competencia,
        coalesce(a.pedidos, 0) as pedidos_mes,
        coalesce(b.pedidos, 0) as pedidos_mes_anterior,
        p.primeira_competencia
    from {{ ref('dim_meses') }} m
    join {{ ref('dim_clientes') }} c
        on c.vigencia_inicio < m.fim_exclusivo
        and (c.vigencia_fim >= m.fim_exclusivo or c.vigencia_fim is null)
    left join compras a on a.id_cliente = c.id_cliente and a.competencia = m.competencia
    left join compras b on b.id_cliente = c.id_cliente
        and b.competencia = (m.competencia - interval '1 month')::date
    left join primeira_compra p on p.id_cliente = c.id_cliente
)
select *,
    case
        when pedidos_mes = 0 then 'sem_compra'
        when primeira_competencia = competencia then 'novo'
        when pedidos_mes_anterior > 0 then 'recorrente'
        else 'reativado'
    end as situacao_compra,
    pedidos_mes > 0 and pedidos_mes_anterior > 0 as retido
from carteira
