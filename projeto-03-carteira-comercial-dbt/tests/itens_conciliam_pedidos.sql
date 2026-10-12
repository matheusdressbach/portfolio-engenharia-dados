select p.id_pedido
from {{ ref('fato_pedidos') }} p
join {{ ref('fato_itens_vendas') }} i using (id_pedido)
group by p.id_pedido, p.receita, p.valor_liquido
having sum(i.receita) <> p.receita or sum(i.valor_liquido) <> p.valor_liquido
