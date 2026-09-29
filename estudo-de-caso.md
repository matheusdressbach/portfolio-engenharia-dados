# Análise comercial com BigQuery e reprodução offline

## Problema e objetivo

Construir uma demonstração de engenharia de dados que transforme vendas, metas e previsões em indicadores comerciais, sem depender de serviços pagos para apresentação do portfólio.

## Solução implementada

Dados sintéticos entram na camada raw por SQL. A camada staging organiza e deduplica os registros; dm reúne dimensões de clientes, produtos, vendedores e calendário; comercial reúne fatos e visualizações analíticas. Os datasets estão em São Paulo. O calendário cobre 2025–2028.

As visualizações incluem desempenho executivo e de vendedores, curva ABC, concentração, ciclo e inatividade de clientes, retração, erosão de margem e acurácia de previsão. A ordenação ABC tem desempate por cliente. Retração e erosão exigem meses consecutivos. A acurácia exclui setembro de 2026, último mês observado e incompleto. Os horizontes de previsão são representados por deslocamentos mensais; não constituem modelo de aprendizado de máquina.

## Validação e resultados

Foram criadas 19 tabelas e 11 visualizações. A exportação completa preserva 5.642 registros. As vendas contêm 848 lançamentos, sendo 827 faturados e 21 cancelados. O intervalo observado vai de 01/04/2025 a 27/09/2026.

O reprocessamento local parte dos registros raw exportados, reconstrói receita, custo e margem por lançamento e compara os valores com a tabela fato. Depois verifica os indicadores dos 18 meses, incluindo clientes ativos, metas, ticket médio e margem. Foram conciliados R$ 3.282.277,00 de faturamento e R$ 1.363.789,70 de margem bruta sintéticos.

O verificador também é testado com dados adulterados: preço negativo, referência de cliente ausente, divergência na fato e divergência no agregado mensal devem ser rejeitados.

## Limites e decisões

As metas sintéticas estão muito acima das receitas e produzem sinais de risco; isso demonstra a regra, sem representar diagnóstico de empresa real. As 11 visualizações foram executadas e exportadas, mas a conciliação independente cobre vendas e indicadores executivos mensais, não cada regra comercial individualmente.

Esta versão usa carga completa por SQL. Ingestão PostgreSQL/API, carga incremental, logs operacionais e orquestração Airflow não foram executados. A arquitetura original V0.7 deve ser avaliada separadamente antes de qualquer alegação de pipeline operacional completo.

## Permanência e apresentação

O Sandbox expira recursos; os arquivos locais não. O repositório pode preservar este estudo, SQL, exportações, evidências e o verificador. Este repositório preserva os arquivos e evidências. A publicação no LinkedIn é uma etapa separada. Ao publicar, descreva explicitamente os dados como sintéticos e o pipeline como demonstração da etapa analítica.
