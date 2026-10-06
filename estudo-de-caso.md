# Análise comercial com BigQuery e reprodução offline

## Problema e objetivo

O ponto de partida foi organizar vendas, metas e previsões para responder perguntas comerciais: quanto foi faturado, qual margem restou e como clientes e vendedores se comportaram ao longo dos meses. Usei uma base sintética e o BigQuery Sandbox para poder reproduzir o trabalho sem contratar serviços.

## Solução implementada

Dados sintéticos entram na camada raw por SQL. A camada staging organiza e deduplica os registros; dm reúne dimensões de clientes, produtos, vendedores e calendário; comercial reúne fatos e visualizações analíticas. Os datasets estão em São Paulo. O calendário cobre 2025–2028.

As visualizações incluem desempenho executivo e de vendedores, curva ABC, concentração, ciclo e inatividade de clientes, retração, erosão de margem e acurácia de previsão. A ordenação ABC tem desempate por cliente. Retração e erosão exigem meses consecutivos. A acurácia exclui setembro de 2026, último mês observado e incompleto. Os horizontes de previsão são representados por deslocamentos mensais; não constituem modelo de aprendizado de máquina.

## Validação e resultados

Foram criadas 19 tabelas e 11 visualizações. A exportação completa preserva 5.642 registros. As vendas contêm 848 lançamentos, sendo 827 faturados e 21 cancelados. O intervalo observado vai de 01/04/2025 a 27/09/2026.

O reprocessamento local parte dos registros raw exportados, reconstrói receita, custo e margem por lançamento e compara os valores com a tabela fato. Depois verifica os indicadores dos 18 meses, incluindo clientes ativos, metas, ticket médio e margem. Foram conciliados R$ 3.282.277,00 de faturamento e R$ 1.363.789,70 de margem bruta sintéticos.

O verificador também é testado com dados adulterados: preço negativo, referência de cliente ausente, divergência na fato e divergência no agregado mensal devem ser rejeitados.

## Limites e decisões

As metas sintéticas estão muito acima das receitas e produzem sinais de risco; isso demonstra a regra, sem representar diagnóstico de empresa real. As 11 visualizações foram executadas e exportadas, mas a conciliação independente cobre vendas e indicadores executivos mensais, não cada regra comercial individualmente.

Mantive a carga completa por SQL neste projeto. Para trabalhar ingestão PostgreSQL/API, incremental e Airflow, desenvolvi o [Projeto 2](projeto-02-pipeline-comercial/README.md). Isso permitiu encerrar a parte analítica aqui e tratar a operação do pipeline em um caso separado.

## Permanência e apresentação

As tabelas do Sandbox têm prazo de expiração. Por isso, mantive no repositório os scripts, as exportações e o verificador Python. Esses arquivos permitem conferir os resultados mesmo quando as tabelas não estiverem mais disponíveis na nuvem.
