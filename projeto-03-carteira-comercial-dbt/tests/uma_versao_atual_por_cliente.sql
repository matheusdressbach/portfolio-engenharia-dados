select id_cliente
from {{ ref('dim_clientes') }}
group by id_cliente
having count(*) filter (where vigencia_fim is null) <> 1
