SELECT 'raw.customers' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.raw.customers` t
UNION ALL
SELECT 'raw.products' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.raw.products` t
UNION ALL
SELECT 'raw.salespeople' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.raw.salespeople` t
UNION ALL
SELECT 'raw.orders' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.raw.orders` t
UNION ALL
SELECT 'raw.metas' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.raw.metas` t
UNION ALL
SELECT 'raw.previsoes' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.raw.previsoes` t
UNION ALL
SELECT 'staging.customers' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.staging.customers` t
UNION ALL
SELECT 'staging.products' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.staging.products` t
UNION ALL
SELECT 'staging.salespeople' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.staging.salespeople` t
UNION ALL
SELECT 'staging.orders' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.staging.orders` t
UNION ALL
SELECT 'staging.metas' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.staging.metas` t
UNION ALL
SELECT 'staging.previsoes' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.staging.previsoes` t
UNION ALL
SELECT 'dm.dim_clientes' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.dm.dim_clientes` t
UNION ALL
SELECT 'dm.dim_produtos' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.dm.dim_produtos` t
UNION ALL
SELECT 'dm.dim_vendedores' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.dm.dim_vendedores` t
UNION ALL
SELECT 'dm.dim_calendario' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.dm.dim_calendario` t
UNION ALL
SELECT 'comercial.fato_lancamento_vendas' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.comercial.fato_lancamento_vendas` t
UNION ALL
SELECT 'comercial.fato_metas' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.comercial.fato_metas` t
UNION ALL
SELECT 'comercial.fato_previsao_faturamento' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.comercial.fato_previsao_faturamento` t
UNION ALL
SELECT 'comercial.vw_indicadores_executivos' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.comercial.vw_indicadores_executivos` t
UNION ALL
SELECT 'comercial.vw_concentracao_clientes' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.comercial.vw_concentracao_clientes` t
UNION ALL
SELECT 'comercial.vw_sinais_gestao' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.comercial.vw_sinais_gestao` t
UNION ALL
SELECT 'comercial.vw_ciclo_clientes' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.comercial.vw_ciclo_clientes` t
UNION ALL
SELECT 'comercial.vw_clientes_inativos' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.comercial.vw_clientes_inativos` t
UNION ALL
SELECT 'comercial.vw_curva_abc_clientes' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.comercial.vw_curva_abc_clientes` t
UNION ALL
SELECT 'comercial.vw_performance_vendedores' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.comercial.vw_performance_vendedores` t
UNION ALL
SELECT 'comercial.vw_acuracia_previsao' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.comercial.vw_acuracia_previsao` t
UNION ALL
SELECT 'comercial.vw_retracao_clientes' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.comercial.vw_retracao_clientes` t
UNION ALL
SELECT 'comercial.vw_erosao_margem' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.comercial.vw_erosao_margem` t
UNION ALL
SELECT 'comercial.vw_sinais_inteligencia_comercial' objeto, TO_JSON_STRING(t) registro FROM `fabled-web-509921-g9.comercial.vw_sinais_inteligencia_comercial` t
ORDER BY objeto, registro;