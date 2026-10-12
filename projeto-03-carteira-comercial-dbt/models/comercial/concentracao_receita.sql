with ordenado as (
    select *,
        row_number() over (partition by competencia order by receita_mes desc, id_cliente) as posicao,
        sum(receita_mes) over (partition by competencia) as receita_total_mes,
        count(*) over (partition by competencia) as clientes_carteira
    from {{ ref('comportamento_clientes') }}
)
select competencia, max(receita_total_mes) as receita_total,
    max(clientes_carteira) as clientes_carteira,
    sum(receita_mes) filter (where posicao <= ceil(clientes_carteira * 0.2)) as receita_top_20pct,
    sum(receita_mes) filter (where posicao <= ceil(clientes_carteira * 0.2))
        / nullif(max(receita_total_mes), 0) as participacao_top_20pct,
    sum(power(receita_mes / nullif(receita_total_mes, 0), 2)) as indice_concentracao
from ordenado group by competencia
