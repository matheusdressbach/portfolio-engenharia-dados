select id_cliente, competencia from {{ ref('fato_carteira_mensal') }}
group by id_cliente, competencia having count(*) <> 1
