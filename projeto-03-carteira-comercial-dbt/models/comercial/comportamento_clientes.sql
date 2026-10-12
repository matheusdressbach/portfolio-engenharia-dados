with mensal as (
    select c.*, coalesce(p.receita, 0) as receita_mes
    from {{ ref('fato_carteira_mensal') }} c
    left join (
        select id_cliente, competencia, sum(receita) as receita
        from {{ ref('fato_pedidos') }} group by 1,2
    ) p using (id_cliente, competencia)
), historico as (
    select *,
        avg(receita_mes) over (
            partition by id_cliente order by competencia
            rows between 3 preceding and 1 preceding
        ) as receita_media_3m_anteriores,
        count(*) over (
            partition by id_cliente order by competencia
            rows between 3 preceding and 1 preceding
        ) as meses_base,
        max(case when pedidos_mes > 0 then competencia end) over (
            partition by id_cliente order by competencia
            rows between unbounded preceding and current row
        ) as ultima_competencia_compra,
        sum(receita_mes) over (
            partition by id_cliente order by competencia
            rows between unbounded preceding and current row
        ) as receita_acumulada
    from mensal
)
select *,
    receita_mes / nullif(pedidos_mes, 0) as ticket_medio,
    receita_mes / nullif(receita_media_3m_anteriores, 0) - 1 as variacao_vs_base,
    case when ultima_competencia_compra is not null then
        (extract(year from age(competencia, ultima_competencia_compra)) * 12
        + extract(month from age(competencia, ultima_competencia_compra)))::int
    end as meses_sem_compra,
    case
        when not ativo then 'cadastro_inativo'
        when meses_base < 3 then 'historico_insuficiente'
        when ultima_competencia_compra is null then 'sem_compra_observada'
        when ultima_competencia_compra <= competencia - interval '2 months' then 'ausencia_prolongada'
        when receita_media_3m_anteriores > 0
            and receita_mes < receita_media_3m_anteriores * 0.5 then 'queda_receita'
        else 'sem_alerta'
    end as sinal_atencao
from historico
