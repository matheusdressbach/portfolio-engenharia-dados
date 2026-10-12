with origem as (
    select competencia, sum(receita) as receita from {{ ref('fato_pedidos') }} group by competencia
), resumo as (
    select competencia, sum(receita) as receita from {{ ref('desempenho_vendedores') }} group by competencia
)
select coalesce(o.competencia, r.competencia) as competencia
from origem o full join resumo r using (competencia)
where coalesce(o.receita, 0::numeric) is distinct from coalesce(r.receita, 0::numeric)
