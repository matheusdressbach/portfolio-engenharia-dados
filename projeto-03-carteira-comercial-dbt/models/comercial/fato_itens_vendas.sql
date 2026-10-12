select i.id_item, i.id_pedido, p.id_cliente, p.id_vendedor,
    p.competencia, p.emitido_em, p.status, i.id_produto,
    i.quantidade, i.preco_unitario, i.valor_desconto,
    i.quantidade * i.preco_unitario as valor_bruto,
    i.quantidade * i.preco_unitario - i.valor_desconto as valor_liquido,
    case when p.status = 'faturado'
        then i.quantidade * i.preco_unitario - i.valor_desconto
        else 0::numeric end as receita
from {{ ref('stg_itens_pedidos') }} i
join {{ ref('fato_pedidos') }} p using (id_pedido)
