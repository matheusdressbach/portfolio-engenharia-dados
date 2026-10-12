select id_vendedor, nome
from {{ source('erp', 'vendedores') }}
