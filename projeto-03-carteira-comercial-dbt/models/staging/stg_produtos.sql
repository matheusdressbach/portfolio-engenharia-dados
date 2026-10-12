select id_produto, nome, categoria
from {{ source('erp', 'produtos') }}
