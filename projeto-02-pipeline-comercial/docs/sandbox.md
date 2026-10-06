# Operação sem faturamento

O modo padrão agora é `PIPELINE_DESTINO=local`. PostgreSQL é a origem ERP e a API
fornece metas. A DAG executa o pipeline real, com raw, staging, qualidade,
publicação por chave e watermarks em SQLite persistente no volume `pipeline-dados`.
SQLite usa transação e upsert; o MERGE em SQL BigQuery continua na implementação
original, mas não é executado neste modo.

Para praticar BigQuery sem ativar faturamento, crie um projeto exclusivo e confirme
no console que ele não possui conta de faturamento vinculada. Use `PIPELINE_DESTINO=sandbox`,
`GCP_PROJECT_ID=<id real>` e `BQ_LOCATION=US` no `.env`. Copie suas credenciais ADC
para `secrets/google.json` (arquivo ignorado pelo Git) e recrie os serviços.
A consulta de segurança à Cloud Billing API precisa estar disponível para o usuário;
se retornar erro, a publicação para e preserva os dados locais. Nunca vincule
faturamento para contornar esse erro. A Cloud Billing API pode precisar ser habilitada
no projeto; isso não vincula uma conta de faturamento.

A etapa `sincronizar_sandbox` verifica que o projeto não tem faturamento antes de
criar datasets e carregar tabelas consolidadas. Usa batch load e WRITE_TRUNCATE,
com esquema explícito, sem INSERT, UPDATE, DELETE ou MERGE. Reexecutar a etapa
substitui as tabelas com o estado consolidado, sem duplicar linhas.
As tabelas são atualizadas uma a uma: não há transação entre as seis tabelas.
Se uma carga falhar, reexecute a sincronização antes de consultar os resultados.
O watermark local já está confirmado e a falha de envio não o desfaz.

Os modos local e Sandbox foram pensados para Docker em uma máquina com LocalExecutor.
Não distribua tarefas entre hosts usando esse arquivo SQLite. O modo original
`bigquery` continua disponível, mas exige faturamento e fica fora desta operação.

No Sandbox, tabelas expiram em 60 dias. A documentação atual informa 10 GiB de
armazenamento acumulado durante a vida do Sandbox e 1 TiB de consultas por mês.
Mantenha volumes pequenos e preserve os dados locais para republicação.
Fonte: https://docs.cloud.google.com/bigquery/docs/sandbox

## Rodar primeiro no ambiente local

Na pasta do projeto:

```sh
docker compose up -d --build
```

No Airflow, mantenha a DAG pausada para começar. Abra `vendas_metas_diarias`
e dispare uma execução manual. No modo local, a última etapa apenas retorna.
Confira as sete tarefas verdes e os logs de extração e qualidade.
Depois poderemos ativar o modo Sandbox com o ID do projeto confirmado.
