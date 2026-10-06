# Harmonização da análise comercial

Após a expansão, as metas de setembro/2026 de Ana e Bruno ainda refletiam o teste pequeno. O script `sql/postgres/07_harmonizar_metas.sql` aplica a mesma regra da massa sintética: Ana R$ 23.040 e Bruno R$ 24.480. Não ajusta metas para atingir resultados observados. A atualização passa pelo trigger de timestamp e pela extração incremental da API. A reaplicação não altera os valores nem os timestamps. Um estado inesperado bloqueia a transação.

Execute o script no PostgreSQL e dispare uma nova execução do DAG. Depois execute `sql/bigquery/desempenho_comercial_projeto2.sql` no BigQuery. A consulta considera outubro/2025 a setembro/2026, com 144 combinações de vendedor/mês. A venda de teste de R$ 60 em outubro/2026 permanece na fato para auditoria, fora desta análise de safra.

Valores esperados após sincronização: receita após devoluções da safra R$ 3.983.777,61; metas da safra R$ 3.900.960,00; setembro R$ 371.520,00 em metas. O total geral da fato permanece R$ 3.983.837,61 após devoluções. Validação confirmada pela exportação `job_YsUorbSw3FiXQ3jHkjc8UDVJFBV8.json` do BigQuery: 144 combinações distintas de vendedor/mês, totais reconciliados e metas de Ana e Bruno atualizadas. Atingimento agregado: 102,12%, calculado pela razão entre os totais. Evidência em `docs/evidencias/harmonizacao-confirmada.json`.
