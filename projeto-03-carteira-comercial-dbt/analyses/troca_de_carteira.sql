-- Compare o vendedor do pedido com o cadastro atual: junho deve continuar no vendedor 1.
select p.id_pedido, p.emitido_em, p.id_vendedor as vendedor_na_venda,
    c.id_vendedor as vendedor_atual, p.receita
from {{ ref('fato_pedidos') }} p
join {{ ref('stg_clientes') }} c using (id_cliente)
where p.id_cliente = 1
order by p.emitido_em;
