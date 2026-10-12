with vendas as (
    select competencia, id_vendedor,
        sum(receita) as receita,
        count(*) filter (where status = 'faturado') as pedidos_faturados
    from {{ ref('fato_pedidos') }}
    group by competencia, id_vendedor
), carteira as (
    select competencia, id_vendedor,
        count(*) as clientes_carteira,
        count(*) filter (where ativo) as clientes_cadastro_ativo,
        count(*) filter (where situacao_compra = 'novo') as clientes_novos,
        count(*) filter (where situacao_compra = 'recorrente') as clientes_recorrentes,
        count(*) filter (where situacao_compra = 'reativado') as clientes_reativados,
        count(*) filter (where pedidos_mes = 0) as clientes_sem_compra,
        count(*) filter (where retido) as clientes_retidos,
        count(*) filter (where pedidos_mes_anterior > 0) as clientes_com_compra_anterior
    from {{ ref('fato_carteira_mensal') }}
    group by competencia, id_vendedor
)
select c.*, v.nome,
    coalesce(p.receita, 0::numeric) as receita,
    coalesce(p.pedidos_faturados, 0) as pedidos_faturados,
    round(100.0 * c.clientes_retidos / nullif(c.clientes_com_compra_anterior, 0), 2)
        as retencao_pct
from carteira c
join {{ ref('dim_vendedores') }} v using (id_vendedor)
left join vendas p using (competencia, id_vendedor)
