# Operação do pipeline comercial

## Antes do primeiro ciclo

1. `docker compose config` deve resolver a configuração sem erro.
2. `docker compose run --build --rm --no-deps testes` deve passar, incluindo `DagBag`.
3. `docker compose ps` deve mostrar PostgreSQL, API, webserver e scheduler saudáveis. `airflow-init` deve terminar com código zero.
4. `bootstrap` deve terminar sem erro. Confira região e os datasets `raw`, `staging`, `dm`, `comercial`, `operacao`.
5. Execute uma carga. Confira sucesso em `operacao.execucoes`, dois lançamentos e R$ 430,00 de receita líquida ativa inicial.
6. Repita o mesmo ID/fim pela CLI, com a DAG pausada. Os fatos e watermarks devem permanecer iguais.
7. Rode o movimento da origem e uma janela posterior. Confira os três lançamentos e R$ 330,00 de receita ativa.

Esses passos são aceitação da integração real; os testes com mocks não substituem esse ciclo.

## Falha na API ou PostgreSQL

Abra o log da tarefa de extração no Airflow. A tarefa aguarda os retries antes de falhar definitivamente. Dados que já chegaram à raw permanecem disponíveis, enquanto fatos e watermarks mantêm o último ciclo aprovado. Corrija a disponibilidade e limpe a tarefa falha e suas tarefas descendentes na interface do Airflow. Não limpe `iniciar_execucao` para mudar o período: ele recupera a janela persistida.

Se a conexão ou credencial do BigQuery estiver errada, os registros de falha também podem não ser gravados. O log da tarefa é a primeira evidência nesse caso.

## Falha de qualidade

O erro identifica a entidade, chave e regra. Confira raw/staging usando o ID completo do DagRun em `execucao`. Corrija a origem e atualize `atualizado_em`. Se a correção ainda estiver dentro da janela fixada, limpe **ambas as extrações, staging, qualidade e publicação** da execução falha. Não basta limpar apenas a qualidade quando a origem mudou.

Se o timestamp da correção ficou fora do fim da execução falha, marque aquela execução como abandonada no processo operacional e crie um **novo DagRun com fim posterior à correção**. Os watermarks ainda antigos permitem reler o período necessário. Não edite o fim registrado nem force o watermark. Raw é preservada como evidência.

## Falha durante publicação

Os `MERGE`, watermarks e status de sucesso pertencem à mesma transação. Uma falha antes do commit preserva o estado anterior. O retry imediato da tarefa pode executar novamente o script. Depois de esgotados os retries, o callback marca `falha`: limpe **qualidade e publicação**, para renovar a aprovação antes de publicar.

Se o commit ocorreu mas a tarefa perdeu a resposta, o status no warehouse já será `sucesso`. A repetição do script reconhece esse estado e não reaplica a carga.

## Monitoramento

Os logs são JSON e incluem `execucao`, `etapa`, `entidade`, `registros` e `segundos` nas extrações. Os logs locais ficam no volume `airflow-logs`; no BigQuery, `operacao.execucoes` registra a situação de cada ciclo e `operacao.watermarks` permite medir defasagem por fonte. As consultas em `sql/bigquery/monitoramento.sql` são o ponto de partida.

Uma carga de zero linhas é válida. Ela avança o watermark quando ambas as fontes foram consultadas com sucesso e a qualidade foi aprovada. Um zero inesperado exige investigação do contrato da origem; não é tratado automaticamente como falha de negócio.

## Parar e preservar dados

`docker compose down` para os serviços e preserva os volumes. O SQL de inicialização do PostgreSQL só roda no primeiro volume novo. Se precisar recriar a origem, primeiro exporte os dados que deseja manter; a remoção manual do volume apaga a origem e o banco de metadados do Airflow. Os datasets BigQuery são independentes dos volumes Docker.

## Fora do escopo operacional

Não execute duas CLIs simultaneamente nem CLI e DAG concorrentes. `max_active_runs=1` serializa somente os DagRuns dessa DAG. A API simulada não possui autenticação de produção. Não existem alertas por e-mail, auditoria de identidade, backfill retroativo, reprocessamento de raw com regras novas ou política de retenção nesta versão.
