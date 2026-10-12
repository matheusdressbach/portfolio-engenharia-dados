select i.competencia, p.categoria,
    sum(i.receita) as receita,
    count(distinct i.id_cliente) filter (where i.status = 'faturado') as compradores,
    sum(i.receita) / nullif(sum(sum(i.receita)) over (partition by i.competencia), 0) as participacao
from {{ ref('fato_itens_vendas') }} i
join {{ ref('dim_produtos') }} p using (id_produto)
group by 1,2 order by 1,3 desc;
