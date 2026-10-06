SELECT id, status, fim, atualizado_em, erro
FROM `__PROJETO__.operacao.execucoes` ORDER BY atualizado_em DESC LIMIT 30;

SELECT entidade, valor, TIMESTAMP_DIFF(CURRENT_TIMESTAMP(),valor,HOUR) horas_defasagem
FROM `__PROJETO__.operacao.watermarks` ORDER BY entidade;

SELECT execucao, entidade, COUNT(*) linhas_raw,
 COUNT(DISTINCT CONCAT(chave,'|',CAST(versao AS STRING))) versoes
FROM `__PROJETO__.raw.registros`
GROUP BY 1,2 ORDER BY 1 DESC;
