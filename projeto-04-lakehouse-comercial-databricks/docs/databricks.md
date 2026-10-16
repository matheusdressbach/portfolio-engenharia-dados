# Primeira execução no Databricks Free Edition

Use [Free Edition](https://docs.databricks.com/aws/en/getting-started/free-edition). A primeira entrega não precisa de conta AWS/Azure/GCP, cartão, trial pago ou armazenamento externo. A plataforma aplica cotas; quando elas acabam, é preciso esperar o reinício. Confira as [limitações oficiais](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations).

1. Entre no workspace gratuito e abra um notebook conectado ao compute serverless. Execute `SELECT current_catalog()` em uma célula SQL e anote o catálogo existente.
2. No SQL editor ou notebook, crie `CREATE SCHEMA IF NOT EXISTS <catalogo>.p4_bronze;` e `CREATE VOLUME IF NOT EXISTS <catalogo>.p4_bronze.entrada;`, substituindo `<catalogo>` pelo nome real. O Volume é dedicado aos arquivos deste projeto.
3. Pelo Catalog Explorer, abra o Volume e envie `clientes.jsonl`, `vendedores.jsonl` e `produtos.jsonl` de `dados/`. Crie a pasta `lotes` no Volume e envie os três arquivos de `dados/lotes/` para ela. A [documentação de importação](https://docs.databricks.com/aws/en/getting-started/import-visualize-data) recomenda o upload pela interface para a Free Edition.
4. No Workspace, importe os quatro arquivos de `notebooks/` como notebooks Python **na mesma pasta**. Não execute `00_motor` isoladamente; os demais carregam suas funções por `%run`.
5. Abra `01_processar_lote`. Preencha `catalogo` e `pasta_entrada` com `/Volumes/<catalogo>/p4_bronze/entrada`. Execute `01_inicial`, depois `02_movimento`, depois `03_atrasos_e_correcao`, mudando o widget `lote` entre as execuções. Mantenha `data_corte=2026-09-30` para comparar com a entrega local.
6. Execute `02_conferir_posicao` e `03_analisar_carteira` no mesmo catálogo. Volte ao notebook 1 e processe de novo o lote 2: ele não deve desfazer o cancelamento do pedido 2 nem duplicar faturamentos.
7. Abra as tabelas no Catalog Explorer e confira `p4_bronze`, `p4_silver`, `p4_dm`, `p4_comercial` e `p4_controle`. O prefixo `p4_` isola a demonstração e mantém os nomes de fatos e dimensões próximos dos outros projetos.

## Job com dependências

Depois da execução manual, crie um Job em **Jobs & Pipelines** com duas tarefas de notebook: `processar_lote` (notebook 1) e `conferir_posicao` (notebook 2), a segunda dependendo da primeira. Passe os mesmos parâmetros de catálogo e lote e o caminho do Volume. Comece com execução manual, uma execução por vez e um retry para falhas transitórias. Não agende uma rotina enquanto estiver aprendendo a ler as execuções e as cotas.

O notebook 3 serve para exploração, sem precisar executar a cada lote. Capture uma execução bem-sucedida do Job e os resultados das três consultas antes de apresentar a integração em nuvem como validada.

## O que depende do seu workspace

O teste local executa Spark e Delta Lake, mas não verifica permissões do Unity Catalog, o runtime serverless ou a configuração do Job. Catálogo, Volume, importação e execução na Free Edition precisam ser conferidos no workspace. Não instale `pyspark` ou `delta-spark` no notebook Databricks: a plataforma já fornece essas dependências.
