# Reprodução no BigQuery Sandbox

A reprodução offline é suficiente para consultar e validar o portfólio sem depender da disponibilidade do Sandbox.

Para uma nova execução na nuvem, use um projeto autorizado, sem conta de faturamento vinculada e com cotas disponíveis. O script 01 substitui as tabelas de mesmo nome: execute apenas em ambiente de demonstração onde essa substituição seja desejada.

1. Crie os datasets `raw`, `staging`, `dm`, `comercial` e `controle` na região `southamerica-east1` (São Paulo). No projeto original eles já existem.
2. Se usar outro projeto, substitua `fabled-web-509921-g9` nos três arquivos SQL pelo ID correto.
3. Execute `01-carga-sandbox-executada.sql` no editor BigQuery com local de processamento São Paulo. Confirme sucesso de todas as instruções e das verificações ASSERT.
4. Execute `02-indicadores-sandbox.sql`. Confirme as 11 visualizações e o resultado mensal.
5. Execute `03-exportacao.sql` e salve o resultado em JSON. A exportação usa as colunas `objeto` e `registro`; preserve esse formato para o verificador offline.

Os scripts não usam DML incremental. Não existe agendamento para recriar tabelas ou contornar a expiração. Evite reconstruções repetidas: os limites do Sandbox incluem armazenamento acumulado ao longo da vida do projeto, conforme a documentação oficial.

Verificações desta execução: 19 tabelas, 11 visualizações, 30 objetos exportados, 5.642 linhas no JSON completo e 18 meses no indicador executivo. O dataset controle fica vazio por decisão de escopo.

Referência: https://docs.cloud.google.com/bigquery/docs/sandbox?hl=pt-br
