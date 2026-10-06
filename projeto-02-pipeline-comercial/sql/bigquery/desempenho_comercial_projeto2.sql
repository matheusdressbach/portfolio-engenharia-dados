-- Devoluções atribuídas ao mês da venda original, para comparar receita com metas.
-- Agrega antes dos joins: duas devoluções não duplicam receita ou meta.
WITH devolucoes_por_venda AS (
  SELECT id_lancamento, SUM(valor_devolvido) AS valor_devolvido
  FROM `pipeline-comercial-md.comercial.fato_devolucoes`
  GROUP BY id_lancamento
), vendas_mensais AS (
  SELECT DATE_TRUNC(v.data_venda, MONTH) AS competencia, v.id_vendedor,
    COUNT(*) AS lancamentos,
    COUNTIF(v.cancelado) AS cancelados,
    SUM(IF(v.cancelado, 0, v.valor_liquido)) AS receita_liquida_ativa,
    SUM(COALESCE(d.valor_devolvido, 0)) AS valor_devolvido,
    SUM(IF(v.cancelado, 0, v.valor_liquido) - COALESCE(d.valor_devolvido, 0)) AS receita_apos_devolucoes
  FROM `pipeline-comercial-md.comercial.fato_lancamento_vendas` v
  LEFT JOIN devolucoes_por_venda d USING (id_lancamento)
  GROUP BY competencia, id_vendedor
)
SELECT COALESCE(v.competencia, m.competencia) AS competencia,
  d.nome, d.equipe, d.regiao,
  COALESCE(v.lancamentos, 0) AS lancamentos,
  COALESCE(v.cancelados, 0) AS cancelados,
  COALESCE(v.receita_liquida_ativa, 0) AS receita_liquida_ativa,
  COALESCE(v.valor_devolvido, 0) AS valor_devolvido,
  COALESCE(v.receita_apos_devolucoes, 0) AS receita_apos_devolucoes,
  m.valor_meta,
  ROUND(100 * SAFE_DIVIDE(COALESCE(v.receita_apos_devolucoes, 0), m.valor_meta), 2) AS atingimento_meta_pct
FROM vendas_mensais v
FULL OUTER JOIN `pipeline-comercial-md.comercial.fato_metas_vendedores` m
  ON v.id_vendedor = m.id_vendedor AND v.competencia = m.competencia
JOIN `pipeline-comercial-md.dm.dim_vendedores` d
  ON d.id_vendedor = COALESCE(v.id_vendedor, m.id_vendedor)
-- Safra completa da massa sintética; outubro/2026 fica na consulta de auditoria.
WHERE COALESCE(v.competencia, m.competencia) >= DATE '2025-10-01'
  AND COALESCE(v.competencia, m.competencia) < DATE '2026-10-01'
ORDER BY competencia, nome;
