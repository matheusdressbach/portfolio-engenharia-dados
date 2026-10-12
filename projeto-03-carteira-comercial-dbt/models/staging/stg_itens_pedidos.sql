select id_item, id_pedido, id_produto, quantidade, preco_unitario, valor_desconto
from {{ source('erp', 'itens_pedidos') }}
