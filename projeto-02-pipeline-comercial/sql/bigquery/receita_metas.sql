-- Substitua __PROJETO__ pelo Project ID; vendas e metas agregadas antes do JOIN.
WITH vendas AS (
 SELECT id_vendedor, DATE_TRUNC(data_venda, MONTH) competencia,
        SUM(valor_liquido) receita_liquida, COUNT(*) lancamentos
 FROM `__PROJETO__.comercial.fato_lancamento_vendas`
 WHERE NOT cancelado GROUP BY 1,2
), metas AS (
 SELECT id_vendedor, competencia, SUM(valor_meta) valor_meta
 FROM `__PROJETO__.comercial.fato_metas_vendedores` GROUP BY 1,2
)
SELECT COALESCE(v.id_vendedor,m.id_vendedor) id_vendedor, d.nome,
       COALESCE(v.competencia,m.competencia) competencia,
       COALESCE(v.receita_liquida,0) receita_liquida, m.valor_meta,
       SAFE_DIVIDE(COALESCE(v.receita_liquida,0),m.valor_meta) atingimento_meta
FROM vendas v FULL OUTER JOIN metas m USING (id_vendedor,competencia)
JOIN `__PROJETO__.dm.dim_vendedores` d
 ON d.id_vendedor=COALESCE(v.id_vendedor,m.id_vendedor);
