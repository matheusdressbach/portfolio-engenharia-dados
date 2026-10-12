select competencia, nome, clientes_carteira, clientes_novos,
    clientes_recorrentes, clientes_reativados, clientes_sem_compra, retencao_pct, receita
from {{ ref('desempenho_vendedores') }}
order by competencia, id_vendedor;
