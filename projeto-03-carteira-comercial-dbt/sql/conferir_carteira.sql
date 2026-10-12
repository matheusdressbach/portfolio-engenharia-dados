select id_cliente, id_vendedor, regiao, ativo, vigencia_inicio, vigencia_fim
from dm.dim_clientes where id_cliente in (1, 2, 3)
order by id_cliente, vigencia_inicio;

select id_pedido, emitido_em, id_vendedor, regiao, receita
from comercial.fato_pedidos where id_cliente = 1 order by emitido_em;

select competencia, nome, receita, clientes_novos, clientes_recorrentes,
    clientes_reativados, clientes_sem_compra, retencao_pct
from comercial.desempenho_vendedores order by competencia, id_vendedor;
