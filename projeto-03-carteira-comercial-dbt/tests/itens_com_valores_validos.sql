select * from {{ ref('stg_itens_pedidos') }}
where quantidade is null or quantidade <= 0
   or preco_unitario is null or preco_unitario < 0
   or valor_desconto is null or valor_desconto < 0
   or valor_desconto > quantidade * preco_unitario
