select c.id_cliente, m.competencia
from (select distinct id_cliente from {{ ref('dim_clientes') }}) c
cross join {{ ref('dim_meses') }} m
left join {{ ref('fato_carteira_mensal') }} f using (id_cliente, competencia)
where f.id_cliente is null
