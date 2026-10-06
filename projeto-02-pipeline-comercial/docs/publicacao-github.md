# Publicar no portfólio

## Organização

Este pacote pode ser um repositório próprio ou uma pasta `projeto-02-pipeline-comercial` dentro do portfólio existente. Preserve os arquivos do Projeto 1. No README principal do portfólio, acrescente um link para o README deste projeto.

A configuração atual de GitHub Actions supõe que o projeto está na raiz do repositório. Se estiver numa subpasta, mova o workflow para `.github/workflows` na raiz do portfólio e configure `defaults.run.working-directory: projeto-02-pipeline-comercial` em cada job. O checkout continua na raiz.

## Arquivos a incluir

Inclua README, Dockerfile, docker-compose.yml, .env.example, .gitignore, pyproject.toml, dags, src, tests, sql, scripts, docs e o workflow de testes. O pacote entregue contém esses arquivos. Os resultados de evidência distinguem testes locais, execução Docker e consultas confirmadas no Sandbox.

Não envie `.env`, `secrets`, credenciais Google, logs operacionais, bancos SQLite, volumes Docker ou caches. O `.gitignore` do projeto já exclui esses itens. Credenciais não devem ser enviadas nem para repositórios privados. Revise a lista de arquivos na tela do GitHub antes de concluir o envio.

## Publicação pelo navegador

1. Extraia o ZIP entregue em uma pasta separada do ambiente que contém credenciais.
2. No repositório do portfólio, use **Add file → Upload files** e envie a pasta do Projeto 2. Confirme que arquivos ocultos como `.gitignore` e `.env.example` também foram incluídos; quando necessário, crie-os pelo editor do GitHub.
3. Use a mensagem de commit `Adiciona pipeline comercial com Airflow e BigQuery Sandbox`.
4. Acrescente o link do projeto no README principal e adapte o workflow para a subpasta antes de usar a integração contínua.
5. Abra o README publicado e confira os links para documentação e evidências.

## Como apresentar

Pipeline incremental de vendas, metas e devoluções com PostgreSQL, REST API, Python e Airflow. Validação de qualidade antes da publicação, watermarks transacionais no destino local e sincronização das tabelas consolidadas com BigQuery Sandbox. Base sintética com 5 mil vendas, testes de reexecução, bloqueio por qualidade e recuperação documentados.

O MERGE no BigQuery é uma implementação alternativa; não foi executado no Sandbox. Evite apresentá-lo como uma integração validada em nuvem. O estado de faturamento observado pertence à validação documentada, não a uma verificação contínua fora das execuções.
