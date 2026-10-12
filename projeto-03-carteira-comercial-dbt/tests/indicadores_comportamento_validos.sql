select id_cliente, competencia
from {{ ref('comportamento_clientes') }}
where meses_sem_compra < 0 or meses_base not between 0 and 3
    or (meses_base < 3 and ativo and sinal_atencao <> 'historico_insuficiente')
union all
select 0, competencia from {{ ref('retencao_coortes') }}
where taxa_compra not between 0 and 1 or compradores > clientes_coorte
union all
select 0, competencia from {{ ref('concentracao_receita') }}
where participacao_top_20pct not between 0 and 1
    or indice_concentracao not between 0 and 1
