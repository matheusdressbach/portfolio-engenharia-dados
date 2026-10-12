select
    p.id_pedido, p.id_cliente, p.emitido_em, p.status,
    count(i.id_item) as itens,
    sum(i.quantidade) as quantidade,
    sum(i.quantidade * i.preco_unitario) as valor_bruto,
    sum(i.valor_desconto) as valor_desconto,
    sum(i.quantidade * i.preco_unitario - i.valor_desconto) as valor_liquido
from {{ ref('stg_pedidos') }} p
join {{ ref('stg_itens_pedidos') }} i using (id_pedido)
group by p.id_pedido, p.id_cliente, p.emitido_em, p.status
