select p.id_pedido from {{ ref('stg_pedidos') }} p
left join {{ ref('stg_itens_pedidos') }} i using (id_pedido)
group by p.id_pedido having count(i.id_item) = 0
