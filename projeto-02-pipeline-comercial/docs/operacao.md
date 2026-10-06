# Operação do pipeline comercial

Este guia descreve os modos `local` e `sandbox`, usados nos testes de integração.
A alternativa `bigquery` não foi validada na conta deste projeto.

## Primeiro ciclo

1. Confira a configuração com `docker compose config`.
2. Inicie os serviços com `docker compose up -d --build` e rode `docker compose run --rm testes`.
3. Confira PostgreSQL, API, webserver e scheduler com `docker compose ps`. O serviço `airflow-init` deve terminar com código zero.
4. No Airflow, dispare uma execução manual de `vendas_metas_diarias` e acompanhe as sete tarefas.
5. No cenário inicial, confira dois lançamentos e R$ 430,00 de receita ativa. Repita uma execução sem alterar a origem: os totais devem permanecer iguais.
6. Aplique `sql/postgres/02_simular_movimento.sql` e dispare outra execução. O resultado esperado passa a três lançamentos, um cancelado e R$ 330,00 de receita ativa.

Esses valores são do cenário inicial. Para a base com 5.000 vendas, siga o [guia de ampliação](base-ampliada.md) e compare as consultas de conferência com os resultados documentados.

## Falha na API ou PostgreSQL

Abra o log da tarefa de extração no Airflow. A tarefa tenta novamente antes de falhar definitivamente. Os registros que chegaram à raw permanecem disponíveis; fatos e watermarks mantêm o último ciclo aprovado.

Depois de corrigir a disponibilidade, limpe a tarefa falha e suas descendentes na interface. A tarefa `iniciar_execucao` recupera a janela persistida, por isso limpá-la não muda o período de extração.

## Falha de qualidade

O erro identifica entidade, chave e regra. Confira raw e staging pelo ID completo da execução. Corrija a origem e atualize `atualizado_em`.

Se a correção estiver dentro da janela fixada, limpe as duas extrações, staging, qualidade e publicação. Limpar apenas a qualidade não traz a alteração da origem.

Se a correção tiver timestamp posterior ao fim da janela, crie uma nova execução manual. Os watermarks preservados permitem reler o período. Não force o watermark nem altere o fim registrado. O [teste de qualidade](teste-qualidade.md) mostra esse procedimento com uma meta inválida.

## Falha durante a publicação

No destino local, o upsert dos dados e o avanço dos watermarks usam a mesma transação. Uma falha antes do commit preserva o estado anterior. Se os retries se esgotarem, limpe qualidade e publicação para validar novamente antes de gravar.

Se a gravação terminar e a tarefa perder a resposta, a repetição reconhece a execução já publicada e não reaplica a carga.

No Sandbox, a tarefa `sincronizar_sandbox` envia as tabelas consolidadas uma a uma. Se o envio falhar, reexecute essa tarefa. A publicação local já foi concluída e não é desfeita. Aguarde a sincronização inteira antes de comparar resultados entre tabelas.

## Acompanhar as execuções

Os logs das extrações incluem `execucao`, `etapa`, `entidade`, `registros` e `segundos`. Os logs do Airflow ficam no volume `airflow-logs`; o estado local, no volume `pipeline-dados`.

Uma carga sem registros pode ser válida. O watermark avança quando as fontes foram consultadas e a qualidade foi aprovada. Se o zero for inesperado, confira a janela e o contrato da origem.

As tabelas `operacao.execucoes`, `operacao.watermarks` e as consultas em `sql/bigquery/monitoramento.sql` pertencem à implementação alternativa `bigquery`; elas não são publicadas no Sandbox.

## Parar e preservar os dados

`docker compose down` encerra os serviços e preserva os volumes. A inicialização do PostgreSQL só roda quando o volume é novo. Não use `down -v` para reiniciar o ambiente: esse comando remove os volumes e os dados locais.

Não execute duas CLIs simultaneamente nem uma CLI junto com a DAG. `max_active_runs=1` controla apenas as execuções dessa DAG. A API é uma origem simulada, sem autenticação de produção. Alertas por e-mail, backfill e retenção automática não fazem parte desta versão.
