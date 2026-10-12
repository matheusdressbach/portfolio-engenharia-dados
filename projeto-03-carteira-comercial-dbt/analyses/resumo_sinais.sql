select competencia, sinal_atencao, count(*) as clientes,
    count(*) filter (where pedidos_mes > 0) as clientes_com_compra,
    sum(receita_mes) as receita_mes
from {{ ref('comportamento_clientes') }}
where competencia = date '2025-12-01'
group by 1,2 order by 1,2;
