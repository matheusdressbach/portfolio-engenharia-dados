# Validação do Projeto 2

## Integração confirmada em 3 de outubro de 2026

Resultados enviados pelo usuário durante a execução no Mac:

- Build Docker, PostgreSQL e API saudáveis; Airflow executando a DAG com sete tarefas.
- **56 testes passaram no container**, incluindo importação e dependências da DAG.
- Projeto `pipeline-comercial-md` sem faturamento: HTTP 200, conta vinculada vazia,
  `billingEnabled=false`; BigQuery exibe Sandbox.
- Carga inicial no BigQuery: **2 lançamentos, 0 cancelados, R$ 430,00**.
- Após correção do desconto, cancelamento e inserção: **3 lançamentos, 1 cancelado, R$ 330,00**.
- Nova execução sem alterar a origem manteve os resultados (idempotência).
- Metas extraídas pela API: Ana Martins **R$ 1.200,00**, Bruno Lopes **R$ 800,00**.
- Recuperação da sincronização após Cloud Billing API desabilitada: etapa falhou,
  foi corrigida a configuração de cota, e a reexecução da etapa publicou com sucesso.

A extração manual foi corrigida para usar a data lógica do disparo. As execuções
agendadas continuam usando o fim do intervalo diário. Retries conservam a janela.

## Limites da evidência

O incremento, qualidade e watermark são processados localmente em SQLite persistente.
No Sandbox, a publicação é batch load com substituição das tabelas consolidadas;
MERGE e transações entre tabelas do BigQuery **não foram executados**.
O fluxo original com MERGE permanece como implementação alternativa não validada
nesta conta. Testes de contrato usam mocks para o cliente BigQuery.

A demonstração isolada já cobre rejeição de qualidade e rollback local.
O teste de rejeição pela DAG real foi executado e confirmado pelo usuário:

- Execução `manual__2026-10-04T00:27:41.658523+00:00`: qualidade rejeitou
  `metas/2: id_vendedor sem dimensão`; publicação e sincronização bloqueadas.
- Comparação com o estado anterior: `publicados_preservados=true` e
  `watermarks_preservados=true`.
- Após restaurar o vendedor 2 na origem, execução
  `manual__2026-10-04T00:35:50.101472+00:00`: sete tarefas com sucesso.

O roteiro reproduzível está em `docs/teste-qualidade.md`. As consultas no BigQuery após a recuperação foram confirmadas pelas capturas
enviadas pelo usuário: 3 lançamentos, 1 cancelado, receita ativa de R$ 330,00;
Ana Martins com meta de R$ 1.200,00 e Bruno Lopes com R$ 800,00.

## Evidências

As capturas enviadas pelo usuário confirmam consultas e execuções descritas acima.
Os arquivos históricos `evidencias/demo.*` representam a demonstração isolada,
cujo resultado (4 lançamentos e R$ 600,00) difere do cenário Docker real.

## Ampliação da base comercial

A nova versão acrescenta atributos às dimensões, 4.997 lançamentos de vendas,
142 metas e 180 devoluções. Preserva o caso inicial. A massa foi gerada com semente
42 e validada com o estado anterior, totalizando 5.000 vendas e 144 metas.

Suíte local: **61 testes encontrados, 60 passaram e 1 ignorado (Airflow ausente)**.
Os novos testes executam a massa inteira no destino local, repetem a carga e
confirmam rollback e preservação dos watermarks quando o acumulado devolvido
supera a venda. Conferem também venda inexistente, cancelamento, valores e datas.

Integração da ampliação confirmada pelo usuário: migração e carga PostgreSQL
concluídas, **61 testes passaram no Docker**, e execução
`manual__2026-10-04T00:52:29.826498+00:00` terminou com sete tarefas verdes.
As consultas no Sandbox confirmaram 12 vendedores, 200 clientes, 40 produtos,
5.000 vendas, 144 metas e 180 devoluções; 5.000 chaves distintas, 131 cancelados,
receita líquida ativa de R$ 4.067.384,72 e devoluções de R$ 83.547,11.
A repetição da DAG com a massa ampliada foi confirmada: execução
`manual__2026-10-04T00:57:05.191523+00:00` terminou com sete tarefas verdes e
a consulta manteve 5.000 lançamentos e chaves distintas, 131 cancelados,
receita ativa de R$ 4.067.384,72 e devoluções de R$ 83.547,11.

## Análise comercial reconciliada

A exportação do BigQuery confirmou 144 combinações distintas entre outubro/2025
e setembro/2026. Receita após devoluções: R$ 3.983.777,61; metas: R$ 3.900.960,00;
atingimento agregado: 102,12%. As duas metas do cenário pequeno foram
harmonizadas pela regra do gerador, sem alterar vendas. A venda de teste de R$ 60
de outubro/2026 permanece na fato, fora da análise dos 12 meses.
Veja `evidencias/harmonizacao-confirmada.json`.
