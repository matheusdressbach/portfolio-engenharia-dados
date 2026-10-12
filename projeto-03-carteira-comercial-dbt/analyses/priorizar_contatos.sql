-- Fechamento escolhido explicitamente: não usa a data atual para analisar 2025.
select c.id_cliente, d.nome, v.nome as vendedor, c.sinal_atencao,
    c.meses_sem_compra, c.receita_mes, c.receita_media_3m_anteriores,
    c.receita_acumulada
from {{ ref('comportamento_clientes') }} c
join {{ ref('dim_clientes') }} d using (chave_cliente)
join {{ ref('dim_vendedores') }} v using (id_vendedor)
where c.competencia = date '2025-12-01'
    and c.ativo and c.sinal_atencao in ('queda_receita', 'ausencia_prolongada')
order by c.receita_media_3m_anteriores desc, c.id_cliente;
