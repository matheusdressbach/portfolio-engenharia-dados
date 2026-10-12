select id_pedido, id_cliente, emitido_em, status
from {{ source('erp', 'pedidos') }}
