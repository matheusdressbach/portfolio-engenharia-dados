select p.id_pedido
from {{ ref('fato_pedidos') }} p
join {{ ref('dim_clientes') }} c using (chave_cliente)
where p.id_cliente <> c.id_cliente or p.id_vendedor <> c.id_vendedor
    or p.emitido_em < c.vigencia_inicio
    or (c.vigencia_fim is not null and p.emitido_em >= c.vigencia_fim)
