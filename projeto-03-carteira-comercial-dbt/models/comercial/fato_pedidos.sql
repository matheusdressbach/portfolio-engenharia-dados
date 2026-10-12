select
    p.id_pedido, p.id_cliente, c.chave_cliente,
    c.id_vendedor, c.regiao,
    p.emitido_em,
    date_trunc('month', p.emitido_em)::date as competencia,
    p.status, p.itens, p.quantidade,
    p.valor_bruto, p.valor_desconto, p.valor_liquido,
    case when p.status = 'faturado' then p.valor_liquido else 0::numeric end as receita
from {{ ref('int_pedidos') }} p
left join {{ ref('dim_clientes') }} c
    on p.id_cliente = c.id_cliente
    and p.emitido_em >= c.vigencia_inicio
    and (p.emitido_em < c.vigencia_fim or c.vigencia_fim is null)
