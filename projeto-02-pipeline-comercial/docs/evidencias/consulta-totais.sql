-- Consulta executada no BigQuery Sandbox em 06/10/2026.
SELECT COUNT(*) AS lancamentos,
  COUNT(DISTINCT id_lancamento) AS chaves_distintas,
  COUNTIF(cancelado) AS cancelados,
  SUM(IF(cancelado, 0, valor_liquido)) AS receita_ativa,
  (SELECT SUM(valor_devolvido) FROM `pipeline-comercial-md.comercial.fato_devolucoes`) AS devolucoes
FROM `pipeline-comercial-md.comercial.fato_lancamento_vendas`;
