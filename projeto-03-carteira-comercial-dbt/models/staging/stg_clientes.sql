select id_cliente, nome, id_vendedor, regiao, ativo, atualizado_em
from {{ source('erp', 'clientes') }}
