with primeira as (
    select id_cliente, min(competencia) as coorte
    from {{ ref('fato_pedidos') }} where status = 'faturado' group by 1
), atividade as (
    select p.coorte, c.competencia,
        count(*) as clientes_coorte,
        count(*) filter (where c.pedidos_mes > 0) as compradores,
        sum(c.receita_mes) as receita
    from primeira p join {{ ref('comportamento_clientes') }} c using (id_cliente)
    where c.competencia >= p.coorte group by 1,2
)
select *,
    (extract(year from age(competencia, coorte)) * 12
    + extract(month from age(competencia, coorte)))::int as idade_coorte_meses,
    compradores::numeric / nullif(clientes_coorte, 0) as taxa_compra
from atividade
