select a.id_cliente, a.chave_cliente, b.chave_cliente as outra_versao
from {{ ref('dim_clientes') }} a
join {{ ref('dim_clientes') }} b
    on a.id_cliente = b.id_cliente and a.chave_cliente < b.chave_cliente
    and a.vigencia_inicio < coalesce(b.vigencia_fim, 'infinity'::timestamptz)
    and b.vigencia_inicio < coalesce(a.vigencia_fim, 'infinity'::timestamptz)
