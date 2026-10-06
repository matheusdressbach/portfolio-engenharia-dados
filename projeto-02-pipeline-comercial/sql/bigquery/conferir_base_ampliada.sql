SELECT 'vendedores' AS entidade, COUNT(*) AS registros FROM `__PROJETO__.dm.dim_vendedores`
UNION ALL SELECT 'clientes', COUNT(*) FROM `__PROJETO__.dm.dim_clientes`
UNION ALL SELECT 'produtos', COUNT(*) FROM `__PROJETO__.dm.dim_produtos`
UNION ALL SELECT 'vendas', COUNT(*) FROM `__PROJETO__.comercial.fato_lancamento_vendas`
UNION ALL SELECT 'metas', COUNT(*) FROM `__PROJETO__.comercial.fato_metas_vendedores`
UNION ALL SELECT 'devolucoes', COUNT(*) FROM `__PROJETO__.comercial.fato_devolucoes`;

SELECT COUNT(*) AS lancamentos, COUNT(DISTINCT id_lancamento) AS chaves_distintas,
  COUNTIF(cancelado) AS cancelados,
  SUM(IF(cancelado,0,valor_liquido)) AS receita_liquida_ativa,
  (SELECT SUM(valor_devolvido) FROM `__PROJETO__.comercial.fato_devolucoes`) AS valor_devolvido
FROM `__PROJETO__.comercial.fato_lancamento_vendas`;
