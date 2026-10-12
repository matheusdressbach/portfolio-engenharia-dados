select
    dbt_scd_id as chave_cliente,
    id_cliente, nome, id_vendedor, regiao, ativo,
    dbt_valid_from as vigencia_inicio,
    dbt_valid_to as vigencia_fim
from {{ ref('clientes_carteira') }}
