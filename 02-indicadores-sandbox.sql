-- Camada de indicadores executivos. Uma linha por mês.
CREATE OR REPLACE VIEW `fabled-web-509921-g9.comercial.vw_indicadores_executivos` AS
WITH vendas AS (
  SELECT DATE_TRUNC(data_venda, MONTH) mes_referencia,
    SUM(valor_faturamento) faturamento,
    SUM(valor_margem_bruta) margem_bruta,
    SAFE_DIVIDE(SUM(valor_margem_bruta), SUM(valor_faturamento)) percentual_margem,
    COUNT(DISTINCT id_cliente) clientes_ativos,
    COUNT(DISTINCT id_lancamento) quantidade_lancamentos,
    SAFE_DIVIDE(SUM(valor_faturamento), COUNT(DISTINCT id_lancamento)) ticket_medio
  FROM `fabled-web-509921-g9.comercial.fato_lancamento_vendas`
  WHERE status = 'invoiced'
  GROUP BY 1
), metas AS (
  SELECT mes_referencia, SUM(valor_meta) valor_meta FROM `fabled-web-509921-g9.comercial.fato_metas` GROUP BY 1
), serie AS (
  SELECT v.*, m.valor_meta,
    SAFE_DIVIDE(v.faturamento, m.valor_meta) percentual_atingimento_meta,
    m.valor_meta - v.faturamento gap_meta,
    LAG(v.faturamento, 1) OVER (ORDER BY v.mes_referencia) faturamento_mes_anterior,
    LAG(v.faturamento, 12) OVER (ORDER BY v.mes_referencia) faturamento_ano_anterior
  FROM vendas v LEFT JOIN metas m USING (mes_referencia)
)
SELECT *,
  SAFE_DIVIDE(faturamento - faturamento_mes_anterior, faturamento_mes_anterior) crescimento_mom,
  SAFE_DIVIDE(faturamento - faturamento_ano_anterior, faturamento_ano_anterior) crescimento_yoy,
  CASE
    WHEN percentual_atingimento_meta >= 1 THEN 'Meta atingida'
    WHEN percentual_atingimento_meta >= 0.9 THEN 'Atenção'
    ELSE 'Risco'
  END AS status_meta
FROM serie;

-- Concentração de receita: permite avaliar dependência dos maiores clientes.
CREATE OR REPLACE VIEW `fabled-web-509921-g9.comercial.vw_concentracao_clientes` AS
WITH cliente AS (
  SELECT DATE_TRUNC(data_venda, MONTH) mes_referencia, id_cliente,
    SUM(valor_faturamento) faturamento_cliente
  FROM `fabled-web-509921-g9.comercial.fato_lancamento_vendas`
  WHERE status = 'invoiced'
  GROUP BY 1,2
), ranking AS (
  SELECT *, ROW_NUMBER() OVER(PARTITION BY mes_referencia ORDER BY faturamento_cliente DESC) posicao,
    SUM(faturamento_cliente) OVER(PARTITION BY mes_referencia) faturamento_total
  FROM cliente
)
SELECT mes_referencia,
  SAFE_DIVIDE(SUM(IF(posicao <= 5, faturamento_cliente, 0)), MAX(faturamento_total)) participacao_top5,
  SAFE_DIVIDE(SUM(IF(posicao <= 10, faturamento_cliente, 0)), MAX(faturamento_total)) participacao_top10
FROM ranking GROUP BY 1;

-- Sinais para direcionar investigação gerencial; não substituem decisão humana.
CREATE OR REPLACE VIEW `fabled-web-509921-g9.comercial.vw_sinais_gestao` AS
SELECT mes_referencia, 'META' AS tipo_sinal,
  CASE WHEN status_meta = 'Risco' THEN 'ALTO' WHEN status_meta = 'Atenção' THEN 'MEDIO' ELSE 'OK' END severidade,
  CONCAT('Atingimento da meta: ', CAST(ROUND(percentual_atingimento_meta * 100, 1) AS STRING), '%') descricao
FROM `fabled-web-509921-g9.comercial.vw_indicadores_executivos`
WHERE valor_meta IS NOT NULL;

-- Inteligência comercial para gestão. Mantém fatos e sinais analíticos separados.

-- Ciclo de vida de clientes por mês.
CREATE OR REPLACE VIEW `fabled-web-509921-g9.comercial.vw_ciclo_clientes` AS
WITH vendas_cliente AS (
  SELECT
    DATE_TRUNC(data_venda, MONTH) AS mes_referencia,
    id_cliente,
    SUM(valor_faturamento) AS faturamento,
    SUM(valor_margem_bruta) AS margem_bruta
  FROM `fabled-web-509921-g9.comercial.fato_lancamento_vendas`
  WHERE status = 'invoiced'
  GROUP BY 1, 2
), historico AS (
  SELECT
    *,
    MIN(mes_referencia) OVER (PARTITION BY id_cliente) AS primeiro_mes,
    LAG(mes_referencia) OVER (PARTITION BY id_cliente ORDER BY mes_referencia) AS mes_venda_anterior,
    LAG(faturamento) OVER (PARTITION BY id_cliente ORDER BY mes_referencia) AS faturamento_venda_anterior
  FROM vendas_cliente
)
SELECT
  mes_referencia,
  id_cliente,
  faturamento,
  margem_bruta,
  CASE
    WHEN mes_referencia = primeiro_mes THEN 'NOVO'
    WHEN DATE_DIFF(mes_referencia, mes_venda_anterior, MONTH) >= 3 THEN 'REATIVADO'
    ELSE 'ATIVO'
  END AS status_cliente,
  DATE_DIFF(mes_referencia, mes_venda_anterior, MONTH) AS meses_desde_ultima_compra,
  SAFE_DIVIDE(faturamento - faturamento_venda_anterior, faturamento_venda_anterior) AS variacao_ultima_compra
FROM historico;

-- Clientes sem compra recente: janela de 90 dias em relação à última data disponível na fato.
CREATE OR REPLACE VIEW `fabled-web-509921-g9.comercial.vw_clientes_inativos` AS
WITH referencia AS (
  SELECT MAX(data_venda) AS data_referencia
  FROM `fabled-web-509921-g9.comercial.fato_lancamento_vendas`
  WHERE status = 'invoiced'
), ultima_compra AS (
  SELECT id_cliente, MAX(data_venda) AS data_ultima_compra,
         SUM(valor_faturamento) AS faturamento_historico
  FROM `fabled-web-509921-g9.comercial.fato_lancamento_vendas`
  WHERE status = 'invoiced'
  GROUP BY 1
)
SELECT u.id_cliente, u.data_ultima_compra,
  DATE_DIFF(r.data_referencia, u.data_ultima_compra, DAY) AS dias_sem_compra,
  u.faturamento_historico
FROM ultima_compra u CROSS JOIN referencia r
WHERE DATE_DIFF(r.data_referencia, u.data_ultima_compra, DAY) >= 90;

-- Curva ABC mensal de clientes com base em participação acumulada no faturamento.
CREATE OR REPLACE VIEW `fabled-web-509921-g9.comercial.vw_curva_abc_clientes` AS
WITH base AS (
  SELECT DATE_TRUNC(data_venda, MONTH) AS mes_referencia, id_cliente,
         SUM(valor_faturamento) AS faturamento_cliente
  FROM `fabled-web-509921-g9.comercial.fato_lancamento_vendas`
  WHERE status = 'invoiced'
  GROUP BY 1, 2
), participacao AS (
  SELECT *,
    SAFE_DIVIDE(faturamento_cliente, SUM(faturamento_cliente) OVER (PARTITION BY mes_referencia)) AS participacao,
    SAFE_DIVIDE(
      SUM(faturamento_cliente) OVER (PARTITION BY mes_referencia ORDER BY faturamento_cliente DESC, id_cliente ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
      SUM(faturamento_cliente) OVER (PARTITION BY mes_referencia)
    ) AS participacao_acumulada
  FROM base
)
SELECT *,
  CASE
    WHEN participacao_acumulada <= 0.80 THEN 'A'
    WHEN participacao_acumulada <= 0.95 THEN 'B'
    ELSE 'C'
  END AS curva_abc
FROM participacao;

-- Performance mensal por vendedor. Foco em resultado com qualidade de margem.
CREATE OR REPLACE VIEW `fabled-web-509921-g9.comercial.vw_performance_vendedores` AS
WITH vendas AS (
  SELECT DATE_TRUNC(data_venda, MONTH) AS mes_referencia, id_vendedor,
    SUM(valor_faturamento) AS faturamento,
    SUM(valor_margem_bruta) AS margem_bruta,
    SAFE_DIVIDE(SUM(valor_margem_bruta), SUM(valor_faturamento)) AS percentual_margem,
    COUNT(DISTINCT id_cliente) AS clientes_ativos,
    COUNT(DISTINCT id_lancamento) AS quantidade_lancamentos,
    SAFE_DIVIDE(SUM(valor_faturamento), COUNT(DISTINCT id_lancamento)) AS ticket_medio
  FROM `fabled-web-509921-g9.comercial.fato_lancamento_vendas`
  WHERE status = 'invoiced'
  GROUP BY 1, 2
)
SELECT v.*, m.valor_meta,
  SAFE_DIVIDE(v.faturamento, m.valor_meta) AS percentual_atingimento_meta,
  m.valor_meta - v.faturamento AS gap_meta,
  DENSE_RANK() OVER (PARTITION BY v.mes_referencia ORDER BY v.faturamento DESC) AS ranking_faturamento,
  DENSE_RANK() OVER (PARTITION BY v.mes_referencia ORDER BY v.percentual_margem DESC) AS ranking_margem
FROM vendas v
LEFT JOIN `fabled-web-509921-g9.comercial.fato_metas` m
  ON m.mes_referencia = v.mes_referencia AND m.id_vendedor = v.id_vendedor;

-- Acurácia histórica do forecast. Apenas meses já realizados entram no cálculo.
CREATE OR REPLACE VIEW `fabled-web-509921-g9.comercial.vw_acuracia_previsao` AS
WITH realizado AS (
  SELECT DATE_TRUNC(data_venda, MONTH) AS mes_referencia,
         SUM(valor_faturamento) AS valor_realizado
  FROM `fabled-web-509921-g9.comercial.fato_lancamento_vendas`
  WHERE status = 'invoiced'
  GROUP BY 1
), previsao AS (
  SELECT data_previsao, mes_referencia, horizonte_dias, valor_previsto
  FROM `fabled-web-509921-g9.comercial.fato_previsao_faturamento`
)
SELECT p.data_previsao, p.mes_referencia, p.horizonte_dias, p.valor_previsto,
  r.valor_realizado,
  ABS(p.valor_previsto - r.valor_realizado) AS erro_absoluto,
  SAFE_DIVIDE(ABS(p.valor_previsto - r.valor_realizado), r.valor_realizado) AS erro_percentual_absoluto,
  GREATEST(0, 1 - SAFE_DIVIDE(ABS(p.valor_previsto - r.valor_realizado), r.valor_realizado)) AS acuracia_previsao
FROM previsao p
JOIN realizado r USING (mes_referencia)
WHERE p.mes_referencia < (SELECT DATE_TRUNC(MAX(data_venda), MONTH) FROM `fabled-web-509921-g9.comercial.fato_lancamento_vendas`);

-- Retração de clientes: comparação com o mesmo cliente no mês anterior.
CREATE OR REPLACE VIEW `fabled-web-509921-g9.comercial.vw_retracao_clientes` AS
WITH mensal AS (
  SELECT DATE_TRUNC(data_venda, MONTH) AS mes_referencia, id_cliente,
         SUM(valor_faturamento) AS faturamento,
         SUM(valor_margem_bruta) AS margem_bruta
  FROM `fabled-web-509921-g9.comercial.fato_lancamento_vendas`
  WHERE status = 'invoiced'
  GROUP BY 1, 2
), comparativo AS (
  SELECT *,
    LAG(mes_referencia) OVER (PARTITION BY id_cliente ORDER BY mes_referencia) AS mes_anterior,
    LAG(faturamento) OVER (PARTITION BY id_cliente ORDER BY mes_referencia) AS faturamento_anterior,
    LAG(margem_bruta) OVER (PARTITION BY id_cliente ORDER BY mes_referencia) AS margem_anterior
  FROM mensal
)
SELECT *,
  SAFE_DIVIDE(faturamento - faturamento_anterior, faturamento_anterior) AS variacao_faturamento,
  SAFE_DIVIDE(margem_bruta - margem_anterior, margem_anterior) AS variacao_margem
FROM comparativo
WHERE DATE_DIFF(mes_referencia, mes_anterior, MONTH) = 1
  AND faturamento_anterior IS NOT NULL
  AND SAFE_DIVIDE(faturamento - faturamento_anterior, faturamento_anterior) <= -0.20;

-- Erosão de margem: receita estável/crescente, porém margem percentual deteriora.
CREATE OR REPLACE VIEW `fabled-web-509921-g9.comercial.vw_erosao_margem` AS
WITH mensal AS (
  SELECT DATE_TRUNC(data_venda, MONTH) AS mes_referencia, id_cliente,
    SUM(valor_faturamento) AS faturamento,
    SAFE_DIVIDE(SUM(valor_margem_bruta), SUM(valor_faturamento)) AS percentual_margem
  FROM `fabled-web-509921-g9.comercial.fato_lancamento_vendas`
  WHERE status = 'invoiced'
  GROUP BY 1, 2
), comparativo AS (
  SELECT *,
    LAG(mes_referencia) OVER (PARTITION BY id_cliente ORDER BY mes_referencia) AS mes_anterior,
    LAG(faturamento) OVER (PARTITION BY id_cliente ORDER BY mes_referencia) AS faturamento_anterior,
    LAG(percentual_margem) OVER (PARTITION BY id_cliente ORDER BY mes_referencia) AS margem_anterior
  FROM mensal
)
SELECT *,
  percentual_margem - margem_anterior AS variacao_pontos_margem
FROM comparativo
WHERE DATE_DIFF(mes_referencia, mes_anterior, MONTH) = 1
  AND faturamento >= faturamento_anterior
  AND percentual_margem <= margem_anterior - 0.03;

-- Sinais gerenciais consolidados. Limiares são parâmetros de demonstração, não regras universais.
CREATE OR REPLACE VIEW `fabled-web-509921-g9.comercial.vw_sinais_inteligencia_comercial` AS
SELECT mes_referencia, CAST(id_cliente AS STRING) AS entidade, 'RETRACAO_CLIENTE' AS tipo_sinal,
       'ALTO' AS severidade,
       CONCAT('Faturamento caiu ', CAST(ROUND(ABS(variacao_faturamento) * 100, 1) AS STRING), '% versus a compra/mês anterior.') AS descricao
FROM `fabled-web-509921-g9.comercial.vw_retracao_clientes`
UNION ALL
SELECT mes_referencia, CAST(id_cliente AS STRING), 'EROSAO_MARGEM', 'MEDIO',
       CONCAT('Margem caiu ', CAST(ROUND(ABS(variacao_pontos_margem) * 100, 1) AS STRING), ' p.p. com receita estável/crescente.')
FROM `fabled-web-509921-g9.comercial.vw_erosao_margem`;

SELECT * FROM `fabled-web-509921-g9.comercial.vw_indicadores_executivos` ORDER BY mes_referencia;